"""Fixtures in this file are artificial and are never written to the user's PostgreSQL."""
import importlib
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, func, select
from config import FEATURES
from data_pipeline import scrape_hourly_news, clean_data, run_pipeline
from database import records, load_training_data
from model_inference import RealEstateAI
from retrain_model import train_model, execute_retrain


@pytest.fixture
def db(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'test.db'))
    yield engine
    engine.dispose()


def test_demo_upserts_instead_of_duplicating(db, tmp_path):
    missing = tmp_path / 'missing.pkl'
    first = run_pipeline(engine=db, model_path=missing)
    second = run_pipeline(engine=db, model_path=missing)
    assert list(first.predicted_price) == [2_100_000_000, 3_150_000_000]
    assert second.prediction_method.eq('demo_formula').all()
    with db.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(records)) == 2
    assert load_training_data(db).empty


@pytest.mark.parametrize('area', ['50', '50m2', '50 m²', '50,0 m2', 50])
def test_area_formats(area):
    raw = scrape_hourly_news().iloc[:1].copy()
    raw['area'] = area
    assert clean_data(raw).dien_tich.iloc[0] == 50


@pytest.mark.parametrize(('field', 'value'), [
    ('area', 'unknown'), ('area', '-50'), ('area', 'inf'), ('rooms', 2.5),
    ('rooms', -1), ('latitude', 91), ('longitude', None), ('id', ''), ('title', None),
])
def test_invalid_records_rejected(field, value):
    raw = scrape_hourly_news().iloc[:1].copy()
    raw[field] = value
    with pytest.raises(ValueError):
        clean_data(raw)


def test_duplicate_ids_rejected():
    raw = pd.concat([scrape_hourly_news().iloc[:1]] * 2, ignore_index=True)
    with pytest.raises(ValueError, match='ID trùng'):
        clean_data(raw)


def test_actual_price_requires_explicit_sale_kind():
    raw = scrape_hourly_news().iloc[:1].copy()
    raw['actual_price'] = 2_000_000_000
    with pytest.raises(ValueError, match='price_kind=sale'):
        clean_data(raw)
    raw['price_kind'] = 'sale'
    assert clean_data(raw).actual_price.iloc[0] == 2_000_000_000


def test_csv_without_model_preserves_unknown_predictions(db, tmp_path):
    raw = scrape_hourly_news().iloc[:1].copy()
    raw['id'] = '000001'
    path = tmp_path / 'input.csv'
    raw.to_csv(path, index=False)
    result = run_pipeline(path, engine=db, model_path=tmp_path / 'missing.pkl')
    assert result.id.iloc[0] == '000001'
    assert result.predicted_price.isna().all()
    assert not result.is_demo.any()
    assert load_training_data(db).empty


@pytest.mark.parametrize('identifier', ['NA', 'NULL', '000001'])
def test_csv_preserves_literal_identifiers(db, tmp_path, identifier):
    raw = scrape_hourly_news().iloc[:1].copy()
    raw['id'] = identifier
    raw['actual_price'] = np.nan
    path = tmp_path / 'input.csv'
    raw.to_csv(path, index=False, encoding='utf-8-sig')
    result = run_pipeline(path, engine=db, model_path=tmp_path / 'missing.pkl')
    assert result.id.iloc[0] == identifier
    assert result.actual_price.isna().all()


def test_csv_rejects_duplicate_headers_before_writing(db, tmp_path):
    path = tmp_path / 'duplicate_columns.csv'
    path.write_text('id,title,area,rooms,latitude,longitude,area\n'
                    '1,House,50,2,10.7,106.6,75\n', encoding='utf-8')
    with pytest.raises(ValueError, match='trùng tên cột'):
        run_pipeline(path, engine=db, model_path=tmp_path / 'missing.pkl')
    assert load_training_data(db).empty


@pytest.mark.parametrize('source', [None, '', '   ', ' demo '])
def test_invalid_or_reserved_source_rejected(source):
    with pytest.raises(ValueError):
        clean_data(scrape_hourly_news(), source=source)


def test_source_trimmed_for_consistent_upserts(db, tmp_path):
    path = tmp_path / 'input.csv'
    scrape_hourly_news().to_csv(path, index=False)
    for source in [' csv ', 'csv']:
        result = run_pipeline(path, source=source, engine=db, model_path=tmp_path / 'missing.pkl')
        assert result.source.eq('csv').all()
    with db.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(records)) == 2


def test_corrupt_model_does_not_silently_become_mock(tmp_path):
    path = tmp_path / 'corrupt.pkl'
    path.write_bytes(b'not a joblib model')
    with pytest.raises(ValueError, match='Không đọc được'):
        RealEstateAI(path, allow_demo=True)


def test_minimum_applies_after_filtering_and_preserves_model(tmp_path):
    frame = pd.DataFrame({c: [1.] * 60 for c in FEATURES})
    frame['actual_price'] = 5_000_000_000
    path = tmp_path / 'existing.pkl'
    path.write_bytes(b'existing model')
    assert train_model(frame, path) is None
    assert path.read_bytes() == b'existing model'


def test_training_never_uses_demo_labels(db, tmp_path):
    run_pipeline(engine=db, model_path=tmp_path / 'missing.pkl')
    assert execute_retrain(db, tmp_path / 'must_not_exist.pkl') is None
    assert not (tmp_path / 'must_not_exist.pkl').exists()


def test_csv_training_and_saved_inference_end_to_end(db, tmp_path):
    # Synthetic TEST ONLY observations; the temporary SQLite/file disappear after pytest.
    rng = np.random.default_rng(42)
    count = 100
    raw = pd.DataFrame({
        'id': [f'TEST_{i}' for i in range(count)], 'title': 'TEST FIXTURE',
        'area': rng.integers(30, 180, count), 'rooms': rng.integers(1, 6, count),
        'latitude': 10.7 + rng.random(count) * .1, 'longitude': 106.6 + rng.random(count) * .1,
        'price_kind': 'sale',
    })
    raw['actual_price'] = raw.area * 35_000_000 + raw.rooms * 90_000_000
    path = tmp_path / 'synthetic_test.csv'
    raw.to_csv(path, index=False)
    model_path = tmp_path / 'test_model.pkl'
    run_pipeline(path, engine=db, model_path=model_path, source='test_only')
    data = load_training_data(db)
    assert len(data) == count
    metrics = execute_retrain(db, model_path)
    assert metrics['train_rows'] == 80 and metrics['test_rows'] == 20
    assert all(np.isfinite(metrics[k]) for k in ['mae_vnd', 'rmse_vnd', 'r2'])
    bundle = joblib.load(model_path)
    assert bundle['target'] == 'actual_price' and bundle['currency'] == 'VND'
    fresh = RealEstateAI(model_path)
    assert fresh.method == 'trained_model'
    output = fresh.predict_price(data.head(2))
    assert len(output) == 2 and (output > 0).all()
    result = run_pipeline(path, engine=db, model_path=model_path, source='test_only')
    assert result.prediction_method.eq('trained_model').all()
    with db.connect() as conn:
        assert conn.scalar(select(func.count()).select_from(records)) == 100


def test_import_scheduler_does_not_run_pipeline(monkeypatch):
    import data_pipeline
    def forbidden(*args, **kwargs):
        pytest.fail('Import must not run a job or connect to database.')
    monkeypatch.setattr(data_pipeline, 'run_pipeline', forbidden)
    import run_hourly
    importlib.reload(run_hourly)
    monkeypatch.undo()
    importlib.reload(run_hourly)


def test_scheduler_once_and_recovery(monkeypatch):
    import run_hourly
    called = []
    monkeypatch.setattr(run_hourly, 'run_pipeline', lambda *args, **kwargs: called.append(True))
    assert run_hourly.main(['--once']) == 0 and len(called) == 1
    def broken(*args, **kwargs):
        raise ValueError('Invalid input')
    monkeypatch.setattr(run_hourly, 'run_pipeline', broken)
    assert run_hourly.main(['--once']) == 1
    with pytest.raises(SystemExit):
        run_hourly.main(['--interval', '0'])
