"""Meaningful dataset, time isolation, unit conversion and explanation checks."""
import json
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from backend.kingcounty import (MODEL, ARTIFACTS, load_bundle, prepare_sales,
    temporal_partitions, validate_property, estimate_property, contributions)
from backend.train_kingcounty import quality_gate, import_database
from backend.web_app import create_app


@pytest.fixture(scope='module')
def bundle():
    if not MODEL.exists():
        from backend.train_kingcounty import train
        train()
    return load_bundle()


@pytest.fixture(scope='module')
def example(bundle):
    return json.loads((ARTIFACTS / 'examples.json').read_text(encoding='utf-8'))[0]['input']


def test_time_blocks_have_no_shared_house_and_do_not_use_future():
    data, _ = prepare_sales()
    parts = temporal_partitions(data)
    names = ['train', 'validation', 'calibration', 'test']
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            assert set(parts[first].id).isdisjoint(parts[second].id)
            assert parts[first].sale_date.max() < parts[second].sale_date.min()


def test_reported_test_metrics_and_interval_coverage_reproduce(bundle):
    tests = pd.read_csv(ARTIFACTS / 'test_predictions.csv')
    metrics = bundle['metadata']['test_metrics']
    assert np.isclose(np.abs(tests.price - tests.predicted_usd).mean(), metrics['mae_usd'])
    coverage = ((tests.price >= tests.lower_usd) & (tests.price <= tests.upper_usd)).mean()
    assert np.isclose(coverage, metrics['interval_coverage'])
    assert len(tests) == bundle['metadata']['splits']['test']['rows']


def test_vnd_conversion_per_m2_and_interval_order(example):
    result = estimate_property(example)
    rate = result['exchange_rate']['usd_vnd']
    assert np.isclose(result['predicted_vnd'], result['predicted_usd'] * rate)
    assert np.isclose(result['price_per_m2_vnd'], result['predicted_vnd'] / example['living_m2'])
    assert result['interval_vnd'][0] < result['predicted_vnd'] < result['interval_vnd'][1]


def test_tree_shap_exactly_reconstructs_prediction(example, bundle):
    row = validate_property(example, bundle['metadata'])
    values, base = contributions(bundle['model'], row, bundle['metadata']['features'])
    reconstructed = np.expm1(base[0] + values.iloc[0].sum())
    predicted = bundle['model'].predict(row[bundle['metadata']['features']])[0]
    assert np.isclose(reconstructed, predicted, rtol=2e-5)


@pytest.mark.parametrize('changes', [
    {'latitude': 10.75, 'longitude': 106.65}, {'sale_date': '2026-11-07'},
    {'zipcode': '00000'}, {'bathrooms': 2.1}, {'bedrooms': 2.5},
    {'living_m2': True}, {'living_m2': float('inf')}, {'grade': -1},
    {'year_built': 2020}, {'year_renovated': 1700}, {'price_per_m2': 50000000},
])
def test_out_of_scope_and_target_leakage_inputs_rejected(example, bundle, changes):
    with pytest.raises(ValueError):
        validate_property(example | changes, bundle['metadata'])


def test_comparables_are_earlier_sales_and_exclude_target_house(example):
    result = estimate_property(example)
    assert result['comparables']
    for house in result['comparables']:
        assert house['sale_date'] < example['sale_date']
        assert house['id'] != example['id']
        assert house['distance_km'] >= 0


def test_failed_quality_gate_cannot_replace_existing_model():
    with pytest.raises(ValueError, match='baseline'):
        quality_gate({'r2': .1, 'mae_usd': 110., 'rmse_usd': 120.},
                     {'mae_usd': 100., 'rmse_usd': 115.})


def test_dataset_import_is_idempotent_and_preserves_user_table(tmp_path, bundle):
    data, _ = prepare_sales()
    engine = create_engine('sqlite:///' + str(tmp_path / 'data.db'))
    try:
        with engine.begin() as con:
            con.execute(text('CREATE TABLE user_data (value INTEGER)'))
            con.execute(text('INSERT INTO user_data VALUES (42)'))
        for _ in range(2):
            import_database(data.head(100), bundle['metadata']['exchange_rate']['usd_vnd'], engine)
        with engine.connect() as con:
            assert con.scalar(text('SELECT COUNT(*) FROM kingcounty_sales')) == 100
            assert con.scalar(text('SELECT value FROM user_data')) == 42
    finally:
        engine.dispose()


def test_new_api_persists_only_valid_predictions_and_keeps_legacy(tmp_path, example):
    engine = create_engine('sqlite:///' + str(tmp_path / 'web.db'))
    try:
        client = create_app(engine=engine, model_path=tmp_path / 'missing-legacy.pkl').test_client()
        assert client.get('/').status_code == 200
        assert client.get('/legacy').status_code == 200
        assert client.get('/api/kingcounty/info').json['metadata']['display_currency'] == 'VND'
        assert client.post('/api/kingcounty/predict', json=example | {'sale_date': '2026-11-07'}).status_code == 400
        assert client.get('/api/kingcounty/history').json['items'] == []
        response = client.post('/api/kingcounty/predict', json=example)
        assert response.status_code == 200
        assert len(client.get('/api/kingcounty/history').json['items']) == 1
        assert client.get('/api/status').json['counts']['total'] == 0
        assert client.get('/evidence/not-allowed.txt').status_code == 404
    finally:
        engine.dispose()
