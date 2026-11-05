"""Exercise an empty CI container; writes demo/test rows to that disposable DB."""
import argparse
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(base, path, payload=None, expected=200):
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    headers = {} if payload is None else {'Content-Type': 'application/json'}
    query = Request(base.rstrip('/') + path, data=data, headers=headers)
    try:
        with urlopen(query, timeout=5) as response:
            status, body = response.status, response.read().decode('utf-8')
    except HTTPError as error:
        status, body = error.code, error.read().decode('utf-8')
    if status != expected:
        raise AssertionError(f'{path}: expected {expected}, got {status}: {body[:300]}')
    return body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:18080')
    args = parser.parse_args()
    deadline = time.monotonic() + 60
    while True:
        try:
            status = json.loads(request(args.url, '/api/status'))
            assert status['database'] == {'backend': 'sqlite', 'connected': True}
            break
        except (URLError, OSError, AssertionError) as error:
            if time.monotonic() >= deadline:
                raise RuntimeError('Container did not become ready within 60 seconds') from error
            time.sleep(1)
    assert status['counts']['total'] == 0, 'Smoke test requires a new disposable database'
    assert 'Dự đoán giá nhà' in request(args.url, '/')
    request(args.url, '/static/app.js')
    request(args.url, '/static/app.css')
    for _ in range(2):
        request(args.url, '/api/demo', {})
    status = json.loads(request(args.url, '/api/status'))
    assert status['counts'] == {'total': 2, 'demo': 2, 'real': 0}
    real = dict(mode='real', id='CI-SMOKE-001', title='CI disposable fixture',
                area=50, rooms=2, latitude=10.75, longitude=106.65)
    result = json.loads(request(args.url, '/api/records', real))['item']
    assert result['predicted_price'] is None and result['actual_price'] is None
    assert result['prediction_method'] == 'unavailable'
    invalid = real | {'id': 'CI-INVALID', 'area': -1}
    request(args.url, '/api/records', invalid, expected=400)
    filtered = json.loads(request(args.url, '/api/records?mode=real&q=CI-SMOKE-001'))
    assert filtered['total'] == 1
    assert json.loads(request(args.url, '/api/status'))['counts']['total'] == 3
    print('Container smoke test passed: UI, assets, SQLite, demo upsert, real input, validation, filters.')


if __name__ == '__main__':
    main()
