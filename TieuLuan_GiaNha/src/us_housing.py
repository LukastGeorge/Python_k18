"""US property sales database, coverage and guarded per-house predictions."""
from datetime import date
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/us_housing.sqlite3'
ARTIFACTS = ROOT / 'artifacts/us'
STATES = dict(line.split('|') for line in '''AL|Alabama
AK|Alaska
AZ|Arizona
AR|Arkansas
CA|California
CO|Colorado
CT|Connecticut
DE|Delaware
DC|Washington, D.C.
FL|Florida
GA|Georgia
HI|Hawaii
ID|Idaho
IL|Illinois
IN|Indiana
IA|Iowa
KS|Kansas
KY|Kentucky
LA|Louisiana
ME|Maine
MD|Maryland
MA|Massachusetts
MI|Michigan
MN|Minnesota
MS|Mississippi
MO|Missouri
MT|Montana
NE|Nebraska
NV|Nevada
NH|New Hampshire
NJ|New Jersey
NM|New Mexico
NY|New York
NC|North Carolina
ND|North Dakota
OH|Ohio
OK|Oklahoma
OR|Oregon
PA|Pennsylvania
RI|Rhode Island
SC|South Carolina
SD|South Dakota
TN|Tennessee
TX|Texas
UT|Utah
VT|Vermont
VA|Virginia
WA|Washington
WV|West Virginia
WI|Wisconsin
WY|Wyoming'''.splitlines())
NUMERIC = ['area_sqft', 'bedrooms', 'bathrooms', 'year_built', 'sale_year', 'sale_month']
CATEGORICAL = ['state', 'locality', 'area_kind']
FEATURES = NUMERIC + CATEGORICAL
AREA_LABELS = {'finished': 'Tổng diện tích hoàn thiện', 'gross': 'Tổng diện tích xây dựng (GBA)'}
LIMITATION = ('Đặc điểm nhà là bản ghi hiện tại của cơ quan thuế, chưa được xác nhận đúng tại ngày bán. '
              'Điểm kiểm thử chỉ phục vụ bài học; chưa chứng minh khả năng định giá thực tế trong quá khứ hoặc tương lai.')


def read_sales(db=DB):
    with closing(sqlite3.connect(f'{Path(db).resolve().as_uri()}?mode=ro', uri=True)) as con:
        return pd.read_sql_query('SELECT * FROM sales ORDER BY sale_date, transaction_id', con)


def coverage(data):
    counts = data.groupby(['state', 'sale_year']).size()
    return pd.DataFrame([{'state': state, 'state_name': name, 'year': year,
        'records': int(counts.get((state, year), 0)),
        'status': 'Có mẫu; không đồng nghĩa đầy đủ' if counts.get((state, year), 0) else 'Chưa có dữ liệu'}
        for state, name in STATES.items() for year in range(2016, 2027)])


def clean_sales(data, as_of=None):
    """Fail closed on invalid observations; report removals without invented values."""
    data = data.copy()
    audit = {'input_rows': len(data)}
    dates = pd.to_datetime(data.sale_date, errors='coerce')
    for col in ['price_usd', 'area_sqft', 'bedrooms', 'bathrooms', 'year_built']:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    masks = {
        'invalid_state': ~data.state.isin(STATES),
        'outside_date_range': ~dates.between('2016-01-01', min(str(as_of or date.today()), '2026-12-31')),
        'invalid_price': ~data.price_usd.between(10000, 20000000),
        'invalid_area': ~data.area_sqft.between(200, 20000),
        'invalid_bedrooms': ~data.bedrooms.between(0, 15) | data.bedrooms.mod(1).ne(0),
        'invalid_bathrooms': ~data.bathrooms.between(0.5, 15),
        'invalid_year_built': ~data.year_built.between(1700, dates.dt.year) | data.year_built.mod(1).ne(0),
        'invalid_area_kind': ~data.area_kind.isin(AREA_LABELS),
        'missing_ids': data.property_id.isna() | data.transaction_id.isna() | data.source_id.isna(),
    }
    rejected = pd.Series(False, index=data.index)
    for reason, mask in masks.items():
        audit[reason] = int(mask.sum())
        rejected |= mask
    audit['invalid_rows_removed'] = int(rejected.sum())
    data = data.loc[~rejected].copy()
    data['sale_date'] = dates.loc[data.index].dt.strftime('%Y-%m-%d')
    data['sale_year'] = dates.loc[data.index].dt.year
    data['sale_month'] = dates.loc[data.index].dt.month
    # Conflicting duplicates are excluded, never chosen by row order.
    conflicts = data.groupby('transaction_id').price_usd.nunique()
    conflict_ids = conflicts[conflicts > 1].index
    audit['conflicting_transaction_rows'] = int(data.transaction_id.isin(conflict_ids).sum())
    data = data.loc[~data.transaction_id.isin(conflict_ids)]
    before = len(data)
    data = data.drop_duplicates('transaction_id').reset_index(drop=True)
    audit['duplicate_rows_removed'] = before - len(data)
    audit['accepted_rows'] = len(data)
    return data, audit


def temporal_split(data):
    """2016–23 train, 2024 validation, 2025–26 test. Purge repeated homes."""
    test = data[data.sale_year >= 2025].copy()
    validation = data[(data.sale_year == 2024) & ~data.property_id.isin(test.property_id)].copy()
    holdout_ids = set(test.property_id) | set(validation.property_id)
    train = data[(data.sale_year <= 2023) & ~data.property_id.isin(holdout_ids)].copy()
    if min(len(train), len(validation), len(test)) < 100:
        raise ValueError('Cần ít nhất 100 giao dịch ở mỗi phần train/validation/test theo thời gian.')
    return train, validation, test


def validate_inputs(frame, meta):
    if frame.empty or len(frame) > 2000:
        raise ValueError('Mỗi lần dự đoán cần 1–2.000 dòng.')
    if frame.columns.duplicated().any() or not set(FEATURES).issubset(frame.columns):
        raise ValueError('CSV thiếu cột hoặc trùng tên cột. Hãy dùng file mẫu mới.')
    clean = frame[FEATURES].copy()
    for col in CATEGORICAL:
        if not clean[col].map(lambda value: isinstance(value, str) and bool(value.strip())).all():
            raise ValueError(f'{col}: phải là mã hoặc tên khu vực hợp lệ, không để trống.')
        clean[col] = clean[col].str.strip()
    for col in NUMERIC:
        clean[col] = pd.to_numeric(clean[col], errors='coerce')
        if not np.isfinite(clean[col]).all():
            raise ValueError(f'{col}: phải là số hữu hạn, không để trống.')
    for col in ['bedrooms', 'year_built', 'sale_year', 'sale_month']:
        if clean[col].mod(1).ne(0).any():
            raise ValueError(f'{col}: phải là số nguyên.')
    for row in clean.to_dict('records'):
        key = row['state'] + '|' + row['locality']
        scope = meta['scopes'].get(key)
        if scope is None or row['area_kind'] != scope['area_kind']:
            raise ValueError('Chưa có mô hình cho bang/khu vực hoặc loại diện tích này.')
        for col in ['area_sqft', 'bedrooms', 'bathrooms', 'year_built']:
            low, high = scope['bounds'][col]
            if not low <= row[col] <= high:
                raise ValueError(f'{col}: ngoài khoảng {low:g}–{high:g} của khu vực.')
        try:
            day = date(int(row['sale_year']), int(row['sale_month']), 1)
        except ValueError as error:
            raise ValueError('Tháng/năm không hợp lệ.') from error
        low = date.fromisoformat(scope['first_date']).replace(day=1)
        high = date.fromisoformat(scope['last_date']).replace(day=1)
        if not low <= day <= high or row['year_built'] > row['sale_year']:
            raise ValueError('Thời điểm định giá ngoài phạm vi dữ liệu hoặc trước năm xây dựng.')
    return clean


def predict_prices(model, frame, meta):
    clean = validate_inputs(frame, meta)
    predictions = np.asarray(model.predict(clean))
    if not np.isfinite(predictions).all() or (predictions <= 0).any():
        raise ValueError('Mô hình không tạo được giá hợp lệ.')
    return clean.assign(PredictedPrice_USD=np.round(predictions, 2))
