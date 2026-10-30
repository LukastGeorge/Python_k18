"""Normalize public sale records into SQLite; never infer a sale price from a listing."""
import hashlib
import json
import sqlite3
from datetime import date, datetime, timezone
import pandas as pd
from src.us_housing import ROOT, DB, ARTIFACTS, STATES, clean_sales, coverage, LIMITATION
from scripts.fetch_us_data import DC, BOULDER

RAW = ROOT / 'data/raw/us'
SOURCES = [
    {'source_id': 'dc_cama', 'state': 'DC', 'locality': 'Washington, D.C.',
     'url': DC, 'description': 'Latest recorded sale per residential property; current CAMA characteristics.',
     'area_kind': 'gross', 'scope': 'Residential properties in Washington, D.C.; selected single-unit records only.'},
    {'source_id': 'boulder_assessor', 'state': 'CO', 'locality': 'Boulder County',
     'url': 'https://bouldercounty.gov/property-and-land/assessor/data-download/',
     'description': 'Qualified sales joined by account to current building records.',
     'area_kind': 'finished', 'scope': 'Boulder County only; single-family homes with one building section.'},
]


def normalize_dc():
    raw = pd.DataFrame(json.loads((RAW / 'dc_residential.json').read_text(encoding='utf-8')))
    duplicates = raw.SSL.duplicated(keep=False)
    sale_dates = pd.to_datetime(raw.SALEDATE, unit='ms', utc=True).dt.tz_convert('America/New_York')
    keep = (raw.QUALIFIED.eq('Q') & raw.NUM_UNITS.eq(1) & raw.BLDG_NUM.eq(1)
            & ~duplicates & raw.STRUCT_D.ne('Multi')
            & (raw.YR_RMDL.fillna(0) <= sale_dates.dt.year))
    d = raw.loc[keep].copy()
    out = pd.DataFrame({
        'transaction_id': 'dc|' + d.SSL.str.strip() + '|' + d.SALE_NUM.astype(str),
        'property_id': 'dc|' + d.SSL.str.strip(), 'source_id': 'dc_cama',
        'state': 'DC', 'locality': 'Washington, D.C.',
        'sale_date': sale_dates.loc[d.index].dt.strftime('%Y-%m-%d'), 'price_usd': d.PRICE,
        'area_sqft': d.GBA, 'area_kind': 'gross', 'bedrooms': d.BEDRM,
        'bathrooms': d.BATHRM + d.HF_BATHRM.fillna(0) * 0.5, 'year_built': d.AYB,
        'feature_snapshot_date': pd.to_datetime(d.GIS_LAST_MOD_DTTM, unit='ms', utc=True).dt.strftime('%Y-%m-%d'),
        'feature_vintage': 'current_snapshot_not_verified_at_sale',
    })
    return out, {'downloaded_rows': len(raw), 'source_filter_removed': int((~keep).sum()),
        'rules': 'Q; one unit/building; unique SSL; non-Multi; remodel year <= sale year.'}


def normalize_boulder():
    buildings = pd.read_csv(RAW / 'boulder_buildings.csv', low_memory=False)
    sales = pd.read_csv(RAW / 'boulder_sales.csv', dtype={'strap': str, 'deedNum': str}, low_memory=False)
    # One building/section per property, so a total transaction is never assigned to one of many buildings.
    buildings = buildings.loc[~buildings.strap.duplicated(keep=False)
        & buildings.bldgClassDscr.eq('SINGLE FAM RES IMPROVEMENTS')].copy()
    dates = pd.to_datetime(sales.Tdate, format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
    sales['sale_date'] = dates.dt.strftime('%Y-%m-%d')
    sales['event'] = sales.deedNum.fillna('') + '|' + sales.sale_date.fillna('')
    parcels = sales.groupby('event').strap.nunique()
    keep = (sales.sales_cd.eq('Q') & sales.status_cd.str.strip().eq('A')
            & sales.deedNum.notna() & sales.event.map(parcels).eq(1)
            & dates.between('2016-01-01', min(str(date.today()), '2026-12-31')))
    joined = sales.loc[keep].merge(buildings, on='strap', validate='many_to_one', suffixes=('_sale', '_building'))
    # Conservative removal where apparent building vintage is later than the sale.
    joined = joined.loc[pd.to_numeric(joined.EffectiveYear, errors='coerce').fillna(0)
                        <= pd.to_datetime(joined.sale_date).dt.year].copy()
    out = pd.DataFrame({
        'transaction_id': 'boulder|' + joined.strap + '|' + joined.event,
        'property_id': 'boulder|' + joined.strap, 'source_id': 'boulder_assessor',
        'state': 'CO', 'locality': 'Boulder County', 'sale_date': joined.sale_date,
        'price_usd': joined.price, 'area_sqft': joined.TotalFinishedSF,
        'area_kind': 'finished', 'bedrooms': joined.nbrBedRoom,
        'bathrooms': joined.nbrFullBaths.fillna(0) + joined.nbrThreeQtrBaths.fillna(0) * 0.75 + joined.nbrHalfBaths.fillna(0) * 0.5,
        'year_built': joined.builtYear, 'feature_snapshot_date': str(date.today()),
        'feature_vintage': 'current_snapshot_not_verified_at_sale',
    })
    return out, {'downloaded_sales': len(sales), 'eligible_building_records': len(buildings),
        'rows_after_source_filters_and_join': len(out),
        'future_sales_removed': int((dates > str(date.today())).sum()),
        'rules': 'Q; active; single-parcel deed; one building/section; single-family; 2016–as_of; effective year <= sale year.'}


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    parts, audit = [], {}
    for name, normalize in [('dc_cama', normalize_dc), ('boulder_assessor', normalize_boulder)]:
        data, source_audit = normalize()
        clean, cleaning = clean_sales(data)
        parts.append(clean)
        audit[name] = {**source_audit, **cleaning}
    data = pd.concat(parts, ignore_index=True).sort_values(['sale_date', 'transaction_id'])
    if data.empty:
        raise RuntimeError('No valid sale records; existing database preserved.')
    temporary = DB.with_suffix('.building.sqlite3')
    if temporary.exists():
        temporary.unlink()
    with sqlite3.connect(temporary) as con:
        con.execute('PRAGMA foreign_keys=ON')
        con.executescript('''
            CREATE TABLE states (state TEXT PRIMARY KEY, state_name TEXT NOT NULL);
            CREATE TABLE sources (source_id TEXT PRIMARY KEY, state TEXT NOT NULL REFERENCES states(state),
              locality TEXT NOT NULL, url TEXT NOT NULL, description TEXT, area_kind TEXT, scope TEXT);
            CREATE TABLE sales (
              transaction_id TEXT PRIMARY KEY, property_id TEXT NOT NULL,
              source_id TEXT NOT NULL REFERENCES sources(source_id), state TEXT NOT NULL REFERENCES states(state),
              locality TEXT NOT NULL, sale_date TEXT NOT NULL CHECK(sale_date >= '2016-01-01' AND sale_date <= '2026-12-31'),
              price_usd REAL NOT NULL CHECK(price_usd > 0), area_sqft REAL NOT NULL CHECK(area_sqft > 0),
              area_kind TEXT NOT NULL CHECK(area_kind IN ('gross','finished')), bedrooms REAL NOT NULL,
              bathrooms REAL NOT NULL, year_built REAL NOT NULL, feature_snapshot_date TEXT,
              feature_vintage TEXT NOT NULL, sale_year INTEGER NOT NULL, sale_month INTEGER NOT NULL);
            CREATE INDEX sales_region_date ON sales(state, locality, sale_date);
            CREATE INDEX sales_property ON sales(property_id);
        ''')
        con.executemany('INSERT INTO states VALUES (?,?)', STATES.items())
        pd.DataFrame(SOURCES).to_sql('sources', con, if_exists='append', index=False)
        data.to_sql('sales', con, if_exists='append', index=False, chunksize=5000)
        coverage(data).to_sql('coverage', con, index=False)
        if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('SQLite integrity check failed.')
    con.close()
    temporary.replace(DB)
    coverage(data).to_csv(ARTIFACTS / 'coverage_by_state_year.csv', index=False, encoding='utf-8-sig')
    summary = {'as_of': str(date.today()), 'target_years': [2016, 2026], 'target_regions': 51,
        'available_regions': sorted(data.state.unique()), 'missing_regions': sorted(set(STATES) - set(data.state)),
        'rows': len(data), 'first_date': data.sale_date.min(), 'last_date': data.sale_date.max(),
        'database_sha256': hashlib.sha256(DB.read_bytes()).hexdigest(),
        'built_at': datetime.now(timezone.utc).isoformat(), 'limitation': LIMITATION, 'audit': audit, 'sources': SOURCES}
    (ARTIFACTS / 'data_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
