import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import date
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from src.us_housing import (ROOT, DB, ARTIFACTS, STATES, FEATURES, coverage, read_sales,
                            clean_sales, temporal_split, predict_prices, validate_inputs)


@pytest.fixture(scope='module')
def sales():
    return read_sales()


@pytest.fixture(scope='module')
def bundle():
    return joblib.load(ARTIFACTS / 'model.joblib'), json.loads((ARTIFACTS / 'metadata.json').read_text(encoding='utf-8'))


@pytest.fixture
def sample():
    return pd.read_csv(ROOT / 'data/us_sample_input.csv').iloc[:1].copy()


def test_sqlite_integrity_and_coverage(sales, bundle):
    with closing(sqlite3.connect(DB)) as con:
        assert con.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert not con.execute('PRAGMA foreign_key_check').fetchall()
        assert con.execute('SELECT COUNT(*) FROM states').fetchone()[0] == 51
    assert len(STATES) == 51 and 'DC' in STATES and 'PR' not in STATES
    cov = coverage(sales)
    assert len(cov) == 51 * 11
    assert cov.records.sum() == len(sales)
    assert not cov[cov.state == 'CA'].records.any()
    assert not sales.transaction_id.duplicated().any()
    assert sales.sale_date.max() <= str(date.today())
    assert sales.sale_year.between(2016, 2026).all()
    assert hashlib.sha256(DB.read_bytes()).hexdigest() == bundle[1]['database_sha256']


def test_time_split_and_property_disjoint(sales):
    train, val, test = temporal_split(sales)
    assert train.sale_date.max() < val.sale_date.min() < test.sale_date.min()
    assert not set(train.property_id) & set(val.property_id)
    assert not set(train.property_id) & set(test.property_id)
    assert not set(val.property_id) & set(test.property_id)


def test_clean_rejects_future_non_us_and_invalid_features(sales):
    good = sales.iloc[:1].copy()
    bad = pd.concat([good] * 4, ignore_index=True)
    bad['transaction_id'] = ['bad1', 'bad2', 'bad3', 'bad4']
    bad.loc[0, 'sale_date'] = '2027-01-01'
    bad.loc[1, 'state'] = 'PR'
    bad.loc[2, 'area_sqft'] = np.inf
    bad.loc[3, 'bedrooms'] = 2.5
    clean, audit = clean_sales(pd.concat([good, bad], ignore_index=True))
    assert len(clean) == 1
    assert audit['invalid_rows_removed'] == 4


def test_conflicting_sale_prices_are_not_silently_chosen(sales):
    frame = pd.concat([sales.iloc[:1]] * 2, ignore_index=True)
    frame.loc[1, 'price_usd'] += 100
    clean, audit = clean_sales(frame)
    assert clean.empty and audit['conflicting_transaction_rows'] == 2


@pytest.mark.parametrize(('column', 'value'), [
    ('state', 'CA'), ('state', None), ('area_kind', 'living'), ('locality', 'Denver'),
    ('area_sqft', -1), ('area_sqft', np.inf), ('bedrooms', 2.3),
    ('bedrooms', 'abc'), ('sale_year', 2027), ('sale_month', 13), ('sale_month', 0),
])
def test_invalid_prediction_rejected(bundle, sample, column, value):
    sample[column] = value
    with pytest.raises(ValueError):
        validate_inputs(sample, bundle[1])


def test_input_schema_and_size(bundle, sample):
    for frame in [sample.iloc[:0], sample.drop(columns='state'), pd.concat([sample] * 2001)]:
        with pytest.raises(ValueError):
            validate_inputs(frame, bundle[1])


def test_single_batch_consistent_and_unit_conversion(bundle, sample):
    model, meta = bundle
    one = predict_prices(model, sample, meta).PredictedPrice_USD.iloc[0]
    batch = predict_prices(model, pd.concat([sample, sample]), meta)
    assert batch.PredictedPrice_USD.tolist() == [one, one]
    sample.area_sqft = (sample.area_sqft * 0.09290304 / 0.09290304).round(6)
    assert predict_prices(model, sample, meta).PredictedPrice_USD.iloc[0] == one


def test_evaluation_artifact_reproduces_report(sales, bundle):
    saved = pd.read_csv(ARTIFACTS / 'test_predictions.csv')
    evaluation_model = joblib.load(ARTIFACTS / 'evaluation_model.joblib')
    inputs = sales.set_index('transaction_id').loc[saved.transaction_id, FEATURES]
    predictions = evaluation_model.predict(inputs)
    assert np.allclose(saved.predicted_usd, predictions)
    meta = bundle[1]
    assert mean_absolute_error(saved.price_usd, predictions) == pytest.approx(meta['test_metrics']['mae'])
    assert root_mean_squared_error(saved.price_usd, predictions) == pytest.approx(meta['test_metrics']['rmse'])
    scores = pd.read_csv(ARTIFACTS / 'validation_metrics.csv')
    assert scores.loc[scores.rmse.idxmin(), 'model'] == meta['selected_model']


def test_us_app_pages_predictions_and_missing_state():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=60).run()
    assert not app.exception
    for page in ['Khám phá dữ liệu', 'Độ phủ 51 khu vực', 'Đánh giá mô hình', 'Dự đoán giá nhà']:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
    app.button[0].click().run()
    assert not app.exception and 'Giá dự đoán:' in app.success[0].value
    app.selectbox(key='us_state').set_value('DC').run()
    app.button[0].click().run()
    assert not app.exception and 'Giá dự đoán:' in app.success[0].value
    app.selectbox(key='us_state').set_value('CA').run()
    assert not app.exception and not app.button
    assert any('Chưa có dữ liệu' in w.value for w in app.warning)
