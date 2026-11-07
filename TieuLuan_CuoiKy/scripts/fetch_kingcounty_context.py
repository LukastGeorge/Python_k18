"""Download auditable FX and pre-sale OpenStreetMap snapshots, without invented POIs."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'real_estate_ai'
DEST = ROOT / 'data' / 'context'
FX_URL = 'https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=1'
SNAPSHOT = '2014-05-01T00:00:00Z'
QUERY = ('[out:json][timeout:45][date:"' + SNAPSHOT + '"];('
         'nwr["amenity"="school"](47.0,-122.7,47.95,-121.1);'
         'nwr["shop"="convenience"](47.0,-122.7,47.95,-121.1);'
         'nwr["shop"="supermarket"](47.0,-122.7,47.95,-121.1););out center tags;')


def download(url, body=None):
    request = Request(url, data=body, headers={
        'User-Agent': 'KingCountyStudentResearch/1.0 (educational snapshot)',
        'Content-Type': 'application/x-www-form-urlencoded'})
    with urlopen(request, timeout=55) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=['fx', 'osm', 'schools', 'all'], default='all')
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    if args.only == 'schools':
        from zipfile import ZipFile
        from io import BytesIO
        url = 'https://nces.ed.gov/ccd/data/zip/sc131a_txt.zip'
        payload = download(url)
        archive = ZipFile(BytesIO(payload))
        print('NCES files', archive.namelist(), flush=True)
        (DEST / 'nces_2013_schools.zip').write_bytes(payload)
        (DEST / 'nces_manifest.json').write_text(json.dumps({'source_url': url,
            'school_year': '2013-2014', 'sha256': hashlib.sha256(payload).hexdigest(),
            'retrieved_at': datetime.now(timezone.utc).isoformat()}, indent=2), encoding='utf-8')
        return
    if args.only in ('fx', 'all'):
        payload = download(FX_URL)
        tree = ET.fromstring(payload)
        usd = next(node for node in tree.iter() if node.attrib.get('CurrencyCode') == 'USD')
        rate = float(usd.attrib['Sell'].replace(',', ''))
        if not 10000 <= rate <= 100000:
            raise ValueError('Unexpected USD/VND quote; manual verification required.')
        timestamp = next((n.text for n in tree.iter() if n.tag == 'DateTime'), None)
        (DEST / 'vietcombank.xml').write_bytes(payload)
        (DEST / 'exchange_rate.json').write_text(json.dumps({
            'usd_vnd': rate, 'quote_kind': 'Vietcombank USD sell',
            'source_url': FX_URL, 'source_page': 'https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-tien-ich/Ty-gia',
            'quoted_at': timestamp, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'sha256': hashlib.sha256(payload).hexdigest(),
            'meaning': 'Currency conversion of historical US house prices; not a Vietnamese market valuation.'
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        print('FX', rate, timestamp, flush=True)
    if args.only in ('osm', 'all'):
        last_error = None
        for endpoint in ['https://api.ohsome.org/v1/elements/centroid', 'https://overpass.private.coffee/api/interpreter']:
            print('Requesting historical OSM', endpoint, flush=True)
            try:
                params = ({'bboxes': '-122.7,47.0,-121.1,47.95', 'time': SNAPSHOT,
                           'filter': 'amenity=school or shop=convenience or shop=supermarket',
                           'properties': 'tags,metadata'} if 'ohsome' in endpoint else {'data': QUERY})
                payload = download(endpoint + '?' + urlencode(params))
                content = json.loads(payload)
                if 'ohsome' in endpoint:
                    elements = []
                    for feature in content.get('features', []):
                        props = feature['properties']
                        lon, lat = feature['geometry']['coordinates']
                        osm_type = props.get('@osmType', props.get('@osmtype', 'node'))
                        elements.append({'type': osm_type, 'id': props.get('@osmId', props.get('@osmid')),
                                         'lat': lat, 'lon': lon,
                                         'tags': {k: v for k, v in props.items() if not k.startswith('@')}})
                    content = {'elements': elements, 'source': 'ohsome API historical centroids'}
                    (DEST / 'ohsome_original.geojson').write_bytes(payload)
                    payload = json.dumps(content, ensure_ascii=False).encode('utf-8')
                if content.get('remark') or not content.get('elements'):
                    raise ValueError('Missing or incomplete historical OSM result: ' + str(content.get('remark')))
                (DEST / 'osm_20140501.json').write_bytes(payload)
                (DEST / 'osm_manifest.json').write_text(json.dumps({
                    'endpoint': endpoint, 'query': params, 'snapshot_at': SNAPSHOT,
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'elements': len(content['elements']), 'sha256': hashlib.sha256(payload).hexdigest(),
                    'attribution': '© OpenStreetMap contributors', 'license': 'ODbL 1.0',
                    'license_url': 'https://www.openstreetmap.org/copyright',
                    'limitations': 'Historical OSM coverage is incomplete. Distances to mapped POI centers are straight-line, not walking routes or school attendance boundaries.'
                }, ensure_ascii=False, indent=2), encoding='utf-8')
                print('OSM elements', len(content['elements']), flush=True)
                return
            except Exception as error:
                last_error = error
                print(type(error).__name__, str(error), flush=True)
        raise RuntimeError('No historical OSM snapshot obtained; never fill with invented distances.') from last_error


if __name__ == '__main__':
    main()
