import json
import math
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from backend.vietnam import ARTIFACTS, FEATURES, load_bundle, estimate_property, validate_property, prepare_listings, grouped_split
from backend.kaggle_vietnam import parse_address
from backend.web_app import create_app
from backend.import_vietnam_data import import_catalog


@pytest.fixture(scope='module')
def vn():
    return load_bundle()


@pytest.fixture(scope='module')
def examples():
    return json.loads((ARTIFACTS / 'examples.json').read_text(encoding='utf-8'))


def test_group_holdouts_are_disjoint_and_excluded_from_serving_fit(vn):
    splits = json.loads((ARTIFACTS / 'split.json').read_text(encoding='utf-8'))
    names = list(splits)
    for index, left in enumerate(names):
        for right in names[index + 1:]:
            assert not set(splits[left]) & set(splits[right])
    serving_ids = set(vn['comparables'].listing_id)
    assert serving_ids == set(splits['train']) | set(splits['validation'])
    assert not serving_ids & set(splits['calibration'] + splits['test'])
    data = pd.read_csv(ARTIFACTS / 'listings_clean.csv.gz')
    for index,left in enumerate(names):
        for right in names[index+1:]:
            assert not set(data.loc[data.listing_id.isin(splits[left]),'group_id']) & set(data.loc[data.listing_id.isin(splits[right]),'group_id'])
    assert vn['metadata']['time_validation'] is False
    assert data.published_at.isna().all()
    assert not set(FEATURES) & {'price', 'price_per_m2', 'description', 'name'}


@pytest.mark.parametrize('index', range(2))
def test_both_cities_predict_with_additive_explanations(examples, vn, index):
    payload = examples[index]['input']
    result = estimate_property(payload)
    reconstructed = math.exp(result['base_log_vnd'] + sum(x['log_contribution'] for x in result['explanations']))
    # XGBoost's native contributions and tree sums use float32; hundreds of
    # trees can differ by a few 1e-5 log units due to accumulation order.
    assert abs(math.log(result['predicted_vnd']) - math.log(reconstructed)) < 5e-5
    assert result['predicted_vnd'] == pytest.approx(reconstructed, rel=5e-5)
    assert result['price_per_m2_vnd'] * payload['area'] == pytest.approx(result['predicted_vnd'])
    assert result['interval_90_vnd'][0] < result['predicted_vnd'] < result['interval_90_vnd'][1]
    assert result['amenities']['available'] is False
    for comp in result['comparables']:
        assert comp['listing_id'] != payload['reference_id']
        assert comp['published_at'] is None and result['comparable_cutoff'] is None
        assert comp['district_name'] == payload['district_name']


@pytest.mark.parametrize('changes', [
    {'province_name': 'Đà Nẵng'}, {'district_name': 'Không có quận này'},
    {'ward_name': 'Phường ngoài phạm vi'}, {'property_type_name': 'Đất'},
    {'area': True}, {'area': -1}, {'area': float('nan')}, {'area': float('inf')},
    {'area': None}, {'bedroom_count': 2.5}, {'road_width': 1000},
    {'price': 5e9}, {'price_per_m2': 1e8}, {'reference_id': '<script>'},
])
def test_invalid_scope_and_leaking_target_fields_rejected(examples, vn, changes):
    with pytest.raises(ValueError):
        validate_property(examples[0]['input'] | changes, vn['metadata'])


def test_optional_missing_fields_are_supported(examples):
    payload = examples[1]['input'] | {key: None for key in ['bedroom_count', 'bathroom_count',
        'frontage_width', 'road_width', 'floor_count']}
    result = estimate_property(payload)
    assert math.isfinite(result['predicted_vnd'])
    assert any('thiếu' in warning for warning in result['warnings'])


def test_reported_test_scores_match_held_out_predictions(vn):
    results = pd.read_csv(ARTIFACTS / 'test_predictions.csv')
    ape = np.abs(results.predicted_vnd - results.price) / results.price
    assert len(results) == vn['metadata']['test']['n']
    assert float(ape.median()) == pytest.approx(vn['metadata']['test']['median_ape'])
    coverage = ((results.price >= results.lower_90_vnd) & (results.price <= results.upper_90_vnd)).mean()
    assert coverage == pytest.approx(vn['metadata']['test']['coverage_90'])


def test_vietnam_routes_persist_valid_results_and_preserve_reference_and_legacy(tmp_path, examples):
    engine = create_engine('sqlite:///' + str(tmp_path / 'web.db'))
    try:
        client = create_app(engine=engine).test_client()
        assert 'TP.HCM' in client.get('/').text
        assert 'King County' in client.get('/kingcounty').text
        assert client.get('/legacy').status_code == 200
        assert client.get('/api/vietnam/info').json['metadata']['currency'] == 'VND'
        bad = client.post('/api/vietnam/predict', json=examples[0]['input'] | {'price': 1e9})
        assert bad.status_code == 400
        assert client.get('/api/vietnam/history').json['items'] == []
        response = client.post('/api/vietnam/predict', json=examples[1]['input'])
        assert response.status_code == 200
        assert len(client.get('/api/vietnam/history').json['items']) == 1
        with engine.begin() as con:
            con.execute(text("INSERT INTO vietnam_predictions (id,created_at,model_version) VALUES ('old-source','2099-01-01','previous-dataset')"))
        assert len(client.get('/api/vietnam/history').json['items']) == 1
        with engine.connect() as con:
            assert con.scalar(text('SELECT COUNT(*) FROM vietnam_predictions')) == 2
        assert client.get('/api/kingcounty/history').json['items'] == []
        assert client.get('/api/status').json['counts']['total'] == 0
        assert client.get('/vietnam-evidence/../../model.joblib').status_code == 404
        assert client.post('/api/vietnam/predict', json=[]).status_code == 400
        assert client.post('/api/vietnam/predict', json=examples[1]['input'], headers={'Origin':'https://example.com'}).status_code == 403
    finally:
        engine.dispose()


def test_kaggle_source_unit_and_schema_are_verified(vn):
    data,audit,source = prepare_listings()
    assert audit['raw_rows'] == 30229 and audit['raw_columns'] == 12
    assert source['revision'] == 'kaggle-version-8'
    from backend.kaggle_vietnam import RAW
    raw = pd.read_csv(RAW / source['files'][0]['path'])
    row = data.iloc[0]
    assert row.price == raw.loc[row.source_row,'Price'] * 1e9
    assert 'property_type_name' not in FEATURES and 'balcony_direction' not in FEATURES
    assert len(FEATURES) == 12
    assert audit['accepted_rows'] == vn['metadata']['audit']['accepted_rows']


def test_address_normalization_does_not_invent_location():
    assert parse_address('Đường A, Phường B, Quận Long Biên, Hà Nội.')[0:2] == ('Hà Nội','Long Biên')
    assert parse_address('Phường 11, Tân Bình, Hồ Chí Minh')[2] == 'Phường 11'
    assert parse_address('Đường A, Quận 12, Hồ Chí Minh')[1:] == ('Quận 12','Không rõ')
    assert parse_address('Chỉ có một dòng')[0] is None


def test_group_split_keeps_reposts_together_and_is_reproducible():
    data = pd.read_csv(ARTIFACTS / 'listings_clean.csv.gz')
    a,b = grouped_split(data),grouped_split(data)
    for key in a:
        assert a[key].listing_id.tolist() == b[key].listing_id.tolist()
    split_by_id = {row:key for key,part in a.items() for row in part.listing_id}
    grouped = data.assign(split=data.listing_id.map(split_by_id)).groupby('group_id').split.nunique()
    assert grouped.max() == 1


def test_observed_catalog_import_is_idempotent_and_preserves_existing_tables(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'catalog.db'))
    small = tmp_path / 'small.csv'
    pd.read_csv(ARTIFACTS / 'listings_clean.csv.gz', dtype={'listing_id':str}).head(12).to_csv(small, index=False)
    try:
        with engine.begin() as con:
            con.execute(text('CREATE TABLE user_data (value INTEGER)'))
            con.execute(text('INSERT INTO user_data VALUES (42)'))
        assert import_catalog(engine, small) == 12
        assert import_catalog(engine, small) == 12
        with engine.connect() as con:
            assert con.scalar(text('SELECT value FROM user_data')) == 42
    finally:
        engine.dispose()
