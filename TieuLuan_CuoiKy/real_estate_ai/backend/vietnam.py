"""Vietnamese asking-price model. Training labels never come from predictions."""
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor, DMatrix

from .config import ROOT
from .kaggle_vietnam import (RAW, CITIES, NUMERIC, CATEGORICAL, FEATURES, LABELS,
    LIMITS, SCOPE, OPTIONAL_CATEGORIES, prepare_listings, grouped_split)

ARTIFACTS = ROOT / 'artifacts/vietnam'
MODEL = ARTIFACTS / 'model.joblib'


def json_write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def normalize_features(frame):
    out = frame[FEATURES].copy()
    for name in NUMERIC:
        out[name] = pd.to_numeric(out[name], errors='coerce').astype(float)
    for name in CATEGORICAL:
        out[name] = out[name].fillna('Không rõ').astype(str)
    return out


def build_regressor(with_location=True):
    cats = CATEGORICAL if with_location else ['house_direction', 'legal_status', 'furniture_state']
    processor = ColumnTransformer([
        ('numeric', Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True,
                                                     keep_empty_features=True))]), NUMERIC),
        ('category', OneHotEncoder(handle_unknown='infrequent_if_exist', min_frequency=10,
                                   sparse_output=True), cats),
    ])
    return Pipeline([('features', processor), ('model', XGBRegressor(
        n_estimators=430, max_depth=6, learning_rate=.055, min_child_weight=12,
        subsample=.85, colsample_bytree=.9, reg_lambda=6, objective='reg:squarederror',
        tree_method='hist', n_jobs=2, random_state=42))])


def fit_baseline(data):
    frame = data.assign(unit=data.price / data.area)
    keys = ['province_name', 'district_name']
    groups = frame.groupby(keys).unit.agg(['median', 'count'])
    local = {'|'.join(key): float(row['median']) for key, row in groups.iterrows() if row['count'] >= 10}
    broad = {key: float(value) for key, value in
             frame.groupby(['province_name']).unit.median().items()}
    return {'local': local, 'broad': broad, 'global': float(frame.unit.median())}


def predict_baseline(data, baseline):
    result = []
    for row in data.to_dict('records'):
        local = '|'.join(row[key] for key in ['province_name', 'district_name'])
        broad = row['province_name']
        result.append(row['area'] * baseline['local'].get(local, baseline['broad'].get(broad, baseline['global'])))
    return np.array(result)


def contributions(pipeline, frame):
    """Aggregate native TreeSHAP values including one-hot and missing indicators."""
    processor = pipeline.named_steps['features']
    encoded = processor.transform(normalize_features(frame))
    booster = pipeline.named_steps['model'].get_booster()
    values = booster.predict(DMatrix(encoded), pred_contribs=True)
    names = processor.get_feature_names_out()
    aggregated = np.zeros((len(frame), len(FEATURES)))
    for col, name in enumerate(names):
        for feature_index, feature in enumerate(FEATURES):
            if name in ('numeric__' + feature, 'numeric__missingindicator_' + feature) or name.startswith('category__' + feature + '_'):
                aggregated[:, feature_index] += values[:, col]
                break
        else:
            raise ValueError('Không ánh xạ được đặc trưng SHAP: ' + name)
    return aggregated, values[:, -1]


@lru_cache(maxsize=4)
def _read_bundle(path, modified):
    return joblib.load(path)


def load_bundle(path=MODEL):
    path = Path(path)
    if not path.exists():
        raise ValueError('Chưa có mô hình Việt Nam. Chạy scripts/huan_luyen.cmd trước.')
    return _read_bundle(str(path.resolve()), path.stat().st_mtime_ns)


def validate_property(payload, meta):
    if not isinstance(payload, dict) or set(payload) - set(FEATURES + ['reference_id']):
        raise ValueError('Chỉ nhận thông tin căn nhà; không nhận giá rao bán hoặc giá/m² làm đầu vào.')
    clean = {}
    for name in CATEGORICAL:
        value = payload.get(name)
        if (name == 'ward_name' or name in OPTIONAL_CATEGORIES) and value in (None, ''):
            value = 'Không rõ'
        if not isinstance(value, str) or len(value) > 100:
            raise ValueError('Thiếu hoặc sai thông tin ' + LABELS[name] + '.')
        clean[name] = value.strip()
    if clean['province_name'] not in CITIES:
        raise ValueError('Chỉ hỗ trợ nhà ở tại TP.HCM hoặc Hà Nội.')
    location = meta['locations'].get(clean['province_name'], {}).get(clean['district_name'])
    if not location:
        raise ValueError('Quận/huyện chưa đủ dữ liệu huấn luyện.')
    if clean['ward_name'] != 'Không rõ' and clean['ward_name'] not in location['wards']:
        raise ValueError('Phường/xã không thuộc danh mục đã học của quận/huyện này.')
    for name, choices in OPTIONAL_CATEGORIES.items():
        if clean[name] not in choices + ['Không rõ']:
            raise ValueError(LABELS[name] + ' không nằm trong danh mục nguồn.')
    for name in NUMERIC:
        value = payload.get(name)
        if value in (None, '') and name != 'area':
            clean[name] = None
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise ValueError(LABELS[name] + ' phải là số.')
        try:
            number = float(value)
        except (ValueError, TypeError):
            raise ValueError(LABELS[name] + ' phải là số.') from None
        low, high = LIMITS[name]
        if not math.isfinite(number) or not low <= number <= high:
            raise ValueError(f'{LABELS[name]} phải từ {low} đến {high}.')
        if name in ('bedroom_count', 'bathroom_count', 'floor_count') and not number.is_integer():
            raise ValueError(LABELS[name] + ' phải là số nguyên.')
        clean[name] = number
    ref = payload.get('reference_id')
    if ref is not None and (not isinstance(ref, str) or len(ref) != 24 or any(c not in '0123456789abcdef' for c in ref)):
        raise ValueError('Mã căn tham khảo không hợp lệ.')
    clean['reference_id'] = ref
    return clean


def estimate_property(payload, path=MODEL):
    bundle = load_bundle(path)
    meta = bundle['metadata']
    clean = validate_property(payload, meta)
    frame = normalize_features(pd.DataFrame([clean]))
    log_price = float(bundle['pipeline'].predict(frame)[0])
    price = float(np.exp(log_price))
    effects, base = contributions(bundle['pipeline'], frame)
    q = bundle['calibration_q']
    warnings = [SCOPE]
    missing = [LABELS[name] for name in NUMERIC if clean[name] is None]
    if missing:
        warnings.append('Đang thiếu ' + ', '.join(missing).lower() + '; mô hình dùng giá trị điền từ tập huấn luyện và cờ thiếu.')
    if clean['area'] < location_range(meta, clean)[0] or clean['area'] > location_range(meta, clean)[1]:
        warnings.append('Diện tích ngoài khoảng 1%–99% quan sát cho thành phố này; dự đoán có thể kém ổn định.')
    comparable = bundle['comparables']
    candidates = comparable[(comparable.province_name == clean['province_name'])
        & (comparable.district_name == clean['district_name'])
        & comparable.listing_id.ne(clean['reference_id'])].copy()
    if not candidates.empty:
        candidates['similarity'] = np.abs(np.log(candidates.area / clean['area']))
        for name in ['bedroom_count', 'bathroom_count']:
            if clean[name] is not None:
                candidates['similarity'] += .08 * (candidates[name] - clean[name]).abs().fillna(3)
        if clean['ward_name'] != 'Không rõ':
            candidates['similarity'] += .3 * candidates.ward_name.ne(clean['ward_name'])
        candidates = candidates.sort_values('similarity').head(5)
    columns = ['listing_id', 'group_id', 'published_at', 'district_name', 'ward_name',
               'area', 'bedroom_count', 'bathroom_count', 'price']
    return {'predicted_vnd': price, 'price_per_m2_vnd': price / clean['area'],
        'interval_90_vnd': [float(np.exp(log_price - q)), float(np.exp(log_price + q))],
        'model_version': meta['model_version'], 'target': 'asking_price_vnd',
        'base_log_vnd': float(base[0]), 'base_price_vnd': float(np.exp(base[0])),
        'explanations': sorted([{'feature': name, 'label': LABELS[name], 'log_contribution': float(effects[0, i])}
                               for i, name in enumerate(FEATURES)], key=lambda item: abs(item['log_contribution']), reverse=True),
        'comparables': candidates[columns].astype(object).where(pd.notna(candidates[columns]), None).to_dict('records'),
        'comparable_cutoff': None,
        'amenities': {'available': False, 'reason': 'Nguồn không có tọa độ và khoảng cách tiện ích đã xác minh. Mô hình không dùng trường học/cửa hàng.'},
        'warnings': warnings}


def location_range(meta, clean):
    return meta['area_ranges'][clean['province_name']]
