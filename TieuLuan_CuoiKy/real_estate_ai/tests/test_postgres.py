"""CI-only PostgreSQL integration; a unique schema isolates test data."""
import os
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, text
from backend.database import load_training_data
from backend.web_app import create_app


@pytest.fixture
def postgres_db():
    url = os.getenv('TEST_POSTGRES_URL')
    if not url:
        pytest.skip('Set TEST_POSTGRES_URL to run PostgreSQL integration')
    schema = 'ci_' + uuid4().hex
    admin = create_engine(url, hide_parameters=True)
    scoped = None
    created = False
    try:
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA {schema}'))
        created = True
        scoped = create_engine(url, hide_parameters=True,
                               connect_args={'options': f'-csearch_path={schema}'})
        yield scoped
    finally:
        if scoped is not None:
            scoped.dispose()
        if created:
            with admin.begin() as connection:
                connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        admin.dispose()


def test_postgres_api_roundtrip(postgres_db, tmp_path):
    client = create_app(engine=postgres_db, model_path=tmp_path / 'missing.pkl').test_client()
    for _ in range(2):
        assert client.post('/api/demo', json={}).status_code == 200
    assert client.get('/api/status').json['counts']['total'] == 2
    assert load_training_data(postgres_db).empty
    payload = dict(mode='real', id='000001', title='CI transaction fixture', area=50,
                   rooms=2, latitude=10.75, longitude=106.65, actual_price=2_000_000_000)
    for area in (50, 75):
        result = client.post('/api/records', json=payload | {'area': area})
        assert result.status_code == 200
        assert result.json['item']['predicted_price'] is None
    status = client.get('/api/status').json
    assert status['database']['backend'] == 'postgresql'
    assert status['counts'] == {'total': 3, 'demo': 2, 'real': 1}
    rows = client.get('/api/records?mode=real&q=000001').json['items']
    assert len(rows) == 1 and rows[0]['dien_tich'] == 75
    assert rows[0]['id'] == '000001' and rows[0]['actual_price'] == 2_000_000_000
    assert len(load_training_data(postgres_db)) == 1
