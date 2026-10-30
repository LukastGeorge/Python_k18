"""Download public, property-level records. No account or API key required."""
import argparse
import hashlib
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/us'
DC = 'https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Property_and_Land_WebMercator/FeatureServer/25'
BOULDER = 'https://assessor.boco.solutions/ASR_PublicDataFiles/'


def get_json(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'HousingStudentProject/1.0'}), timeout=60) as response:
                result = json.load(response)
            if 'error' in result:
                raise ValueError(str(result['error']))
            return result
        except (TimeoutError, OSError):
            if attempt == 2:
                raise
            time.sleep(2)


def fetch_dc():
    end = min(date.today(), date(2026, 12, 31))
    where = f"SALEDATE >= DATE '2016-01-01' AND SALEDATE <= DATE '{end.isoformat()}' AND PRICE >= 10000"
    params = {'f': 'json', 'where': where, 'returnGeometry': 'false'}
    expected = get_json(DC + '/query?' + urlencode({**params, 'returnCountOnly': 'true'}))['count']
    fields = 'OBJECTID,SSL,SALEDATE,PRICE,QUALIFIED,SALE_NUM,GBA,BEDRM,BATHRM,HF_BATHRM,AYB,YR_RMDL,NUM_UNITS,BLDG_NUM,LANDAREA,STRUCT_D,GIS_LAST_MOD_DTTM'
    rows = []
    while len(rows) < expected:
        page = get_json(DC + '/query?' + urlencode({**params, 'outFields': fields,
            'orderByFields': 'OBJECTID', 'resultOffset': len(rows), 'resultRecordCount': 2000}))
        values = [r['attributes'] for r in page['features']]
        if not values:
            raise RuntimeError('DC download stopped before expected row count.')
        rows.extend(values)
        print(f'DC: {len(rows)}/{expected}', flush=True)
    if len({r['OBJECTID'] for r in rows}) != len(rows):
        raise RuntimeError('DC returned duplicate IDs; retry snapshot download.')
    path = RAW / 'dc_residential.json'
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
    temp.replace(path)
    return {'file': path.name, 'url': DC, 'query': where, 'rows': len(rows)}


def fetch_boulder(refresh=False):
    outputs = []
    for filename, local in [('Buildings.csv', 'boulder_buildings.csv'), ('Sales.csv', 'boulder_sales.csv')]:
        target = RAW / local
        if refresh or not target.exists():
            temporary = target.with_suffix('.part')
            with urlopen(BOULDER + filename, timeout=120) as response, temporary.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temporary.replace(target)
        outputs.append({'file': local, 'url': BOULDER + filename})
    return outputs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', choices=['dc', 'boulder', 'all'], default='all')
    parser.add_argument('--refresh', action='store_true')
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    outputs = []
    if args.source in ('dc', 'all'):
        outputs.append(fetch_dc())
    if args.source in ('boulder', 'all'):
        outputs.extend(fetch_boulder(args.refresh))
    for item in outputs:
        item.update(sha256=hashlib.sha256((RAW / item['file']).read_bytes()).hexdigest(),
                    downloaded_at=datetime.now(timezone.utc).isoformat())
        manifest[item['file']] = item
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Saved manifest:', manifest_path)


if __name__ == '__main__':
    main()
