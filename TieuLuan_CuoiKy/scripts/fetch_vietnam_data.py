"""Fetch original public Vietnamese listing data with source revision and checksums."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1] / 'real_estate_ai'
DEST = ROOT / 'data/raw/vietnam'
REPOSITORY = 'tinixai/vietnam-real-estates'


def fetch(url, timeout=45):
    with urlopen(Request(url, headers={'User-Agent': 'VietnamHousingAcademic/1.0'}), timeout=timeout) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true')
    parser.add_argument('--shards', type=int, default=1)
    args = parser.parse_args()
    DEST.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(fetch('https://huggingface.co/api/datasets/' + REPOSITORY))
    (DEST / 'repository.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    paths = [item['rfilename'] for item in metadata['siblings'] if item['rfilename'].endswith('.parquet')]
    print('Repository revision', metadata['sha'], 'shards', len(paths), flush=True)
    print('Data files', paths[:10], flush=True)
    readme = fetch('https://huggingface.co/datasets/' + REPOSITORY + '/raw/' + metadata['sha'] + '/README.md')
    (DEST / 'README_source.md').write_bytes(readme)
    if args.inspect:
        url = 'https://datasets-server.huggingface.co/first-rows?dataset=' + REPOSITORY + '&config=default&split=train'
        rows = json.loads(fetch(url))
        (DEST / 'first_rows.json').write_text(json.dumps(rows, ensure_ascii=False), encoding='utf-8')
        print('Columns', [f['name'] for f in rows['features']], flush=True)
        for record in rows['rows'][:5]:
            r = record['row']
            print({k: r.get(k) for k in ['property_type_name', 'province_name', 'district_name', 'price', 'area', 'published_at']}, flush=True)
        return
    manifest = {'repository': REPOSITORY, 'revision': metadata['sha'],
                'source_url': 'https://huggingface.co/datasets/' + REPOSITORY,
                'license': 'CC-BY-NC-4.0', 'target': 'listed price VND, not completed-sale price',
                'retrieved_at': datetime.now(timezone.utc).isoformat(), 'files': []}
    for source_path in paths[:args.shards]:
        target = DEST / Path(source_path).name
        url = 'https://huggingface.co/datasets/' + REPOSITORY + '/resolve/' + metadata['sha'] + '/' + source_path
        if not target.exists():
            print('Downloading', source_path, flush=True)
            payload = fetch(url, timeout=55)
            target.write_bytes(payload)
        manifest['files'].append({'path': target.name, 'source_path': source_path, 'url': url,
                                  'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
        print('Saved', target.name, target.stat().st_size, flush=True)
    (DEST / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
