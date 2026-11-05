"""API tests use temporary SQLite, never the configured user database."""
import joblib
import pytest
from sqlalchemy import create_engine
from backend.config import FEATURES
from backend.database import load_training_data
from backend.web_app import create_app


@pytest.fixture
def web(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'web.db'))
    app = create_app(engine=engine, model_path=tmp_path / 'model.pkl')
    app.config['TESTING'] = True
    yield app.test_client(), engine, tmp_path
    engine.dispose()


def payload(**changes):
    data = dict(mode='demo', id='WEB-001', title='Nhà minh họa', area=50,
                rooms=2, latitude=10.762622, longitude=106.660172)
    return data | changes


def test_ui_and_initial_status(web):
    client, _, tmp_path = web
    response = client.get('/')
    assert response.status_code == 200
    assert 'Dự đoán giá nhà' in response.text
    assert not (tmp_path / 'web.db').exists()
    for path in ('/static/app.js', '/static/app.css', '/static/house.svg'):
        assert client.get(path).status_code == 200
    status = client.get('/api/status')
    assert status.status_code == 200
    assert status.json['counts'] == {'total': 0, 'demo': 0, 'real': 0}
    assert status.json['model']['method'] == 'unavailable'


def test_demo_prediction_persists_and_updates(web):
    client, engine, _ = web
    response = client.post('/api/records', json=payload())
    assert response.status_code == 200
    assert response.json['item']['predicted_price'] == 2_100_000_000
    assert response.json['item']['is_demo'] is True
    updated = client.post('/api/records', json=payload(area=75))
    assert updated.json['item']['predicted_price'] == 3_100_000_000
    assert client.get('/api/status').json['counts']['total'] == 1
    assert client.get('/api/records').json['items'][0]['dien_tich'] == 75
    assert load_training_data(engine).empty


def test_real_input_has_no_fabricated_price_and_keeps_sales_label(web):
    client, engine, _ = web
    result = client.post('/api/records', json=payload(mode='real', actual_price=2_000_000_000))
    assert result.status_code == 200
    row = result.json['item']
    assert row['predicted_price'] is None
    assert row['prediction_method'] == 'unavailable'
    assert row['is_demo'] is False and row['price_kind'] == 'sale'
    assert len(load_training_data(engine)) == 1
    unknown = client.post('/api/records', json=payload(mode='real', id='NA'))
    assert unknown.json['item']['actual_price'] is None
    assert len(load_training_data(engine)) == 1


@pytest.mark.parametrize('changes', [
    {'area': 0}, {'rooms': 1.5}, {'latitude': 91}, {'longitude': None},
    {'id': ''}, {'title': ['invalid']}, {'area': True}, {'actual_price': 2_000_000_000},
    {'mode': 'other'}, {'source': 'demo'}, {'mode': 'real', 'actual_price': -100},
])
def test_invalid_input_does_not_write(web, changes):
    client, _, _ = web
    response = client.post('/api/records', json=payload(**changes))
    assert response.status_code == 400
    assert response.json['error']
    assert client.get('/api/status').json['counts']['total'] == 0


def test_demo_button_is_idempotent_and_search_is_paginated(web, capsys):
    client, _, _ = web
    for _ in range(2):
        assert client.post('/api/demo', json={}).status_code == 200
    assert capsys.readouterr().out == ''
    client.post('/api/records', json=payload(mode='real', title='Nhà thật 100%'))
    assert client.get('/api/status').json['counts'] == {'total': 3, 'demo': 2, 'real': 1}
    first = client.get('/api/records?mode=demo&page_size=1').json
    second = client.get('/api/records?mode=demo&page_size=1&page=2').json
    assert first['total_pages'] == 2 and first['total'] == 2
    assert first['items'][0]['id'] != second['items'][0]['id']
    assert client.get('/api/records?q=100%25').json['total'] == 1
    assert client.get('/api/records?mode=real').json['items'][0]['is_demo'] is False
    assert client.get('/api/records?page=0').status_code == 400
    assert client.get('/api/records?page_size=bad').status_code == 400


def test_same_id_in_real_and_demo_does_not_overwrite(web):
    client, _, _ = web
    client.post('/api/records', json=payload())
    client.post('/api/records', json=payload(mode='real'))
    assert client.get('/api/status').json['counts']['total'] == 2


def test_json_validation_and_same_origin(web):
    client, _, _ = web
    assert client.post('/api/records', data='{}').status_code == 415
    assert client.post('/api/records', json=[]).status_code == 400
    assert client.post('/api/demo', data='{', content_type='application/json').status_code == 400
    assert client.post('/api/demo', json={}, headers={'Origin': 'https://other.example'}).status_code == 403
    assert client.post('/api/demo', json={}, headers={'Origin': 'http://localhost'}).status_code == 200
    assert client.get('/api/missing').is_json


def test_broken_database_keeps_ui_available_and_hides_connection_details(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'missing' / 'database.db'))
    try:
        client = create_app(engine=engine).test_client()
        assert client.get('/').status_code == 200
        response = client.get('/api/status')
        assert response.status_code == 503
        assert '--backend sqlite' in response.json['error']
        assert str(tmp_path) not in response.text
    finally:
        engine.dispose()


def test_corrupt_model_cannot_be_silently_used_as_demo(web):
    client, _, tmp_path = web
    (tmp_path / 'model.pkl').write_bytes(b'broken')
    status = client.get('/api/status').json
    assert status['database']['connected'] is True
    assert status['model']['error']
    assert client.post('/api/records', json=payload()).status_code == 400
    assert client.get('/api/status').json['counts']['total'] == 0


def test_api_uses_saved_trained_model(web):
    from sklearn.dummy import DummyRegressor
    import pandas as pd
    client, _, tmp_path = web
    features = pd.DataFrame([[50, 2, 10.7, 106.6]], columns=FEATURES)
    model = DummyRegressor(strategy='constant', constant=2_345_000_000).fit(features, [2_345_000_000])
    joblib.dump(dict(model=model, features=FEATURES, target='actual_price', currency='VND'), tmp_path / 'model.pkl')
    result = client.post('/api/records', json=payload(mode='real')).json['item']
    assert result['predicted_price'] == 2_345_000_000
    assert result['prediction_method'] == 'trained_model'
    assert client.get('/api/status').json['model']['method'] == 'trained_model'


def test_configured_hosts_are_checked(web, monkeypatch):
    _, engine, tmp_path = web
    monkeypatch.setenv('WEB_TRUSTED_HOSTS', 'localhost, realestate.test')
    client = create_app(engine=engine, model_path=tmp_path / 'missing.pkl').test_client()
    assert client.get('/', base_url='http://realestate.test').status_code == 200
    assert client.get('/', base_url='http://other.test').status_code == 400
