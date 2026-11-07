"""King County historical valuation, auditable currency conversion and explanations."""
from datetime import datetime
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree
from xgboost import DMatrix

from .config import ROOT

RAW = ROOT / 'data/raw/kc_house_data.csv'
CONTEXT = ROOT / 'data/context'
ARTIFACTS = ROOT / 'artifacts/kingcounty'
MODEL = ARTIFACTS / 'model.joblib'
EXPECTED_SHA = 'd0875baa0251b21d4bdc9d2ae940a4fe0bb6009824f23dd0e2a5b2bf04557b7e'
SQFT_TO_M2 = 0.09290304
EARTH_KM = 6371.0088
BASE_FEATURES = ['living_m2', 'bedrooms', 'latitude', 'longitude']
HOUSE_FEATURES = ['living_m2', 'lot_m2', 'bedrooms', 'bathrooms', 'floors', 'waterfront',
                  'view', 'condition', 'grade', 'house_age', 'renovated',
                  'renovation_age', 'latitude', 'longitude', 'month_index', 'zipcode']
POI_FEATURES = ['school_km', 'convenience_km', 'supermarket_km']
LABELS = {
    'living_m2': 'Diện tích ở', 'lot_m2': 'Diện tích đất', 'bedrooms': 'Phòng ngủ',
    'bathrooms': 'Phòng tắm', 'floors': 'Số tầng', 'waterfront': 'Ven nước',
    'view': 'Cảnh quan', 'condition': 'Tình trạng nhà', 'grade': 'Chất lượng xây dựng',
    'house_age': 'Tuổi nhà', 'renovated': 'Đã cải tạo', 'renovation_age': 'Tuổi cải tạo',
    'latitude': 'Vĩ độ', 'longitude': 'Kinh độ', 'month_index': 'Thời điểm giao dịch',
    'zipcode': 'Mã bưu chính', 'school_km': 'Khoảng cách trường học',
    'convenience_km': 'Khoảng cách cửa hàng tiện lợi', 'supermarket_km': 'Khoảng cách siêu thị'}
LIMITATION = ('Ước tính nhà tại King County theo dữ liệu giao dịch 2014–2015, quy đổi sang VND. '
              'Không phải giá nhà Việt Nam hay định giá thị trường hiện tại. '
              'Quan hệ trong dữ liệu và đóng góp mô hình không chứng minh quan hệ nhân quả.')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_fx():
    fx = json.loads((CONTEXT / 'exchange_rate.json').read_text(encoding='utf-8'))
    if not np.isfinite(fx['usd_vnd']) or not 10000 <= fx['usd_vnd'] <= 100000:
        raise ValueError('Tỷ giá USD/VND không hợp lệ.')
    if sha256(CONTEXT / 'vietcombank.xml') != fx['sha256']:
        raise ValueError('Snapshot tỷ giá không khớp checksum.')
    return fx


@lru_cache(maxsize=1)
def points_of_interest():
    path = CONTEXT / 'osm_20140501.json'
    if not path.exists():
        return pd.DataFrame(columns=['kind', 'name', 'latitude', 'longitude', 'osm_id'])
    manifest = json.loads((CONTEXT / 'osm_manifest.json').read_text(encoding='utf-8'))
    if sha256(path) != manifest['sha256'] or manifest['snapshot_at'] != '2014-05-01T00:00:00Z':
        raise ValueError('Snapshot OSM không đúng thời điểm hoặc checksum.')
    rows = []
    for element in json.loads(path.read_text(encoding='utf-8'))['elements']:
        tags = element.get('tags', {})
        kind = 'school' if tags.get('amenity') == 'school' else tags.get('shop')
        if kind not in ('school', 'convenience', 'supermarket'):
            continue
        center = element if 'lat' in element else element.get('center', {})
        if 'lat' not in center or 'lon' not in center:
            continue
        rows.append(dict(kind=kind, name=tags.get('name', 'Chưa ghi tên trên OSM'),
                         latitude=center['lat'], longitude=center['lon'],
                         osm_id=element['type'] + '/' + str(element['id'])))
    frame = pd.DataFrame(rows, columns=['kind', 'name', 'latitude', 'longitude', 'osm_id'])
    # One school may be represented both by a point and by its campus polygon.
    # Distances are nearest-center observations; no POI counts are used as features.
    return frame


def add_poi_distances(frame):
    result = frame.copy()
    poi = points_of_interest()
    for kind in ['school', 'convenience', 'supermarket']:
        group = poi[poi.kind == kind]
        if group.empty:
            result[kind + '_km'] = np.nan
            continue
        tree = BallTree(np.radians(group[['latitude', 'longitude']]), metric='haversine')
        distance, _ = tree.query(np.radians(result[['latitude', 'longitude']]), k=1)
        result[kind + '_km'] = distance[:, 0] * EARTH_KM
    return result


def prepare_sales(raw_path=RAW):
    if sha256(raw_path) != EXPECTED_SHA:
        raise ValueError('Dataset khác snapshot trong notebook. Cần kiểm tra và cập nhật manifest trước khi huấn luyện.')
    raw = pd.read_csv(raw_path, dtype={'id': str, 'zipcode': str})
    data = raw.drop_duplicates().copy()
    if data.duplicated(['id', 'date']).any():
        raise ValueError('Trùng mã nhà và ngày bán với nội dung mâu thuẫn.')
    data['sale_date'] = pd.to_datetime(data.date, format='%Y%m%dT%H%M%S', errors='coerce')
    valid = (data.sale_date.between('2014-05-02', '2015-05-27')
             & data.price.gt(0) & data.sqft_living.between(100, 25000)
             & data.sqft_lot.gt(0) & data.bedrooms.between(0, 15) & data.bedrooms.mod(1).eq(0)
             & data.bathrooms.between(.5, 15) & data.grade.between(1, 13)
             & data.condition.between(1, 5) & data.view.between(0, 4)
             & data.yr_built.between(1800, data.sale_date.dt.year)
             & (data.yr_renovated.eq(0) | data.yr_renovated.between(data.yr_built, data.sale_date.dt.year))
             & data.lat.between(47.0, 48.0) & data.long.between(-123, -121))
    audit = {'raw_rows': len(raw), 'exact_duplicates': len(raw) - len(data),
             'invalid_rows': int((~valid).sum()), 'rejected_ids': data.loc[~valid, 'id'].tolist()}
    data = data.loc[valid].copy()
    data['living_m2'] = data.sqft_living * SQFT_TO_M2
    data['lot_m2'] = data.sqft_lot * SQFT_TO_M2
    data['latitude'], data['longitude'] = data.lat, data.long
    data['house_age'] = data.sale_date.dt.year - data.yr_built
    data['renovated'] = data.yr_renovated.gt(0).astype(int)
    data['renovation_age'] = np.where(data.renovated, data.sale_date.dt.year - data.yr_renovated, 0)
    data['month_index'] = (data.sale_date.dt.year - 2014) * 12 + data.sale_date.dt.month
    data['transaction_id'] = data.id + '|' + data.sale_date.dt.strftime('%Y-%m-%d')
    data = add_poi_distances(data).sort_values(['sale_date', 'id']).reset_index(drop=True)
    audit['accepted_rows'] = len(data)
    audit['unique_houses'] = int(data.id.nunique())
    return data, audit


def temporal_partitions(data):
    """Four sequential, property-disjoint blocks; no information flows backwards."""
    masks = {'test': data.sale_date.ge('2015-03-01'),
             'calibration': data.sale_date.ge('2015-01-01') & data.sale_date.lt('2015-03-01'),
             'validation': data.sale_date.ge('2014-11-01') & data.sale_date.lt('2015-01-01'),
             'train': data.sale_date.lt('2014-11-01')}
    seen, parts = set(), {}
    for name, mask in masks.items():
        part = data.loc[mask & ~data.id.isin(seen)].copy()
        parts[name] = part
        seen.update(part.id)
        if len(part) < 100:
            raise ValueError('Không đủ 100 giao dịch trong tập ' + name)
    return parts


def validate_property(payload, meta):
    if not isinstance(payload, dict):
        raise ValueError('Thông tin căn nhà phải là JSON object.')
    allowed = set(meta['input_defaults']) | {'id', 'sale_date'}
    if set(payload) - allowed:
        raise ValueError('Trường không hỗ trợ: ' + ', '.join(sorted(set(payload) - allowed)))
    required = set(meta['input_defaults']) | {'sale_date'}
    if not required.issubset(payload):
        raise ValueError('Thiếu trường: ' + ', '.join(sorted(required - set(payload))))
    row = {}
    for key in meta['input_defaults']:
        value = payload[key]
        if key == 'zipcode':
            if not isinstance(value, str) or value not in meta['zipcodes']:
                raise ValueError('Mã bưu chính nằm ngoài dữ liệu King County đã học.')
            row[key] = value
            continue
        if isinstance(value, bool):
            raise ValueError(key + ': cần một số, không nhận boolean.')
        try:
            row[key] = float(value)
        except (TypeError, ValueError):
            raise ValueError(key + ': cần một số hữu hạn.') from None
        if not np.isfinite(row[key]):
            raise ValueError(key + ': cần một số hữu hạn.')
        low, high = meta['input_bounds'][key]
        if not low <= row[key] <= high:
            raise ValueError(f'{key}: cần trong khoảng {low:g}–{high:g} theo dữ liệu King County.')
    for key in ['bedrooms', 'waterfront', 'view', 'condition', 'grade', 'year_built', 'year_renovated']:
        if row[key] % 1:
            raise ValueError(key + ': phải là số nguyên.')
    if row['bathrooms'] * 4 % 1 or row['floors'] * 2 % 1:
        raise ValueError('Phòng tắm theo bước 0,25 và số tầng theo bước 0,5.')
    if not isinstance(payload['sale_date'], str):
        raise ValueError('Ngày định giá cần dạng YYYY-MM-DD.')
    try:
        sold = datetime.strptime(payload['sale_date'], '%Y-%m-%d')
    except ValueError:
        raise ValueError('Ngày định giá cần dạng YYYY-MM-DD.') from None
    if not meta['first_date'] <= sold.strftime('%Y-%m-%d') <= meta['last_date']:
        raise ValueError('Chỉ hỗ trợ bối cảnh giao dịch 02/05/2014–27/05/2015. Chưa có mô hình thị trường hiện tại.')
    if row['year_built'] > sold.year or (row['year_renovated'] and not row['year_built'] <= row['year_renovated'] <= sold.year):
        raise ValueError('Năm xây/cải tạo không được sau năm giao dịch hoặc cải tạo trước khi xây.')
    row['house_age'] = sold.year - row['year_built']
    row['renovated'] = int(row['year_renovated'] > 0)
    row['renovation_age'] = sold.year - row['year_renovated'] if row['renovated'] else 0
    row['month_index'] = (sold.year - 2014) * 12 + sold.month
    row['sale_date'] = sold.strftime('%Y-%m-%d')
    return add_poi_distances(pd.DataFrame([row]))


@lru_cache(maxsize=2)
def _load_bundle(path, modified_ns):
    bundle = joblib.load(path)
    if bundle.get('schema') != 'kingcounty-v1' or not hasattr(bundle.get('model'), 'predict'):
        raise ValueError('Mô hình King County sai định dạng.')
    return bundle


def load_bundle(model_path=MODEL):
    path = Path(model_path)
    if not path.exists():
        raise ValueError('Chưa có mô hình King County. Chạy scripts/huan_luyen.cmd trước.')
    return _load_bundle(str(path.resolve()), path.stat().st_mtime_ns)


def contributions(model, features, columns):
    """Exact TreeSHAP contributions in log1p(USD), never causal currency effects."""
    pipeline = model.regressor_
    transformed = pipeline['prepare'].transform(features[columns])
    regressor = pipeline['regressor']
    if not hasattr(regressor, 'get_booster'):
        return None
    values = regressor.get_booster().predict(DMatrix(transformed), pred_contribs=True)
    names = pipeline['prepare'].get_feature_names_out()
    result = pd.DataFrame(index=features.index)
    for key in columns:
        indices = [i for i, name in enumerate(names) if name == 'numeric__' + key or name.startswith('category__' + key + '_')]
        result[key] = values[:, indices].sum(axis=1)
    return result, values[:, -1]


def nearest_amenities(row):
    poi, answer = points_of_interest(), []
    for kind in ['school', 'convenience', 'supermarket']:
        group = poi[poi.kind == kind].reset_index(drop=True)
        if group.empty:
            answer.append({'kind': kind, 'available': False})
            continue
        distance, idx = BallTree(np.radians(group[['latitude', 'longitude']]), metric='haversine').query(
            np.radians(row[['latitude', 'longitude']]), k=1)
        place = group.iloc[int(idx[0, 0])]
        answer.append({'kind': kind, 'available': True, 'name': place['name'],
                       'distance_km': float(distance[0, 0] * EARTH_KM),
                       'latitude': float(place.latitude), 'longitude': float(place.longitude),
                       'osm_url': 'https://www.openstreetmap.org/' + place.osm_id})
    return answer


def comparable_sales(row, reference, rate, exclude_id=None):
    sold = pd.Timestamp(row.sale_date.iloc[0])
    pool = reference.loc[reference.sale_date.lt(sold) & reference.id.ne(str(exclude_id))].copy()
    if pool.empty:
        return []
    distance, _ = BallTree(np.radians(row[['latitude', 'longitude']]), metric='haversine').query(
        np.radians(pool[['latitude', 'longitude']]), k=1)
    pool['distance_km'] = distance[:, 0] * EARTH_KM
    pool['similarity_score'] = (pool.distance_km + 4 * np.abs(np.log(pool.living_m2 / row.living_m2.iloc[0]))
                                + .3 * np.abs(pool.bedrooms - row.bedrooms.iloc[0])
                                + .2 * np.abs(pool.bathrooms - row.bathrooms.iloc[0]))
    answer = []
    for _, house in pool.nsmallest(5, 'similarity_score').iterrows():
        answer.append({'id': house.id, 'sale_date': house.sale_date.strftime('%Y-%m-%d'),
                       'living_m2': float(house.living_m2), 'bedrooms': int(house.bedrooms),
                       'bathrooms': float(house.bathrooms), 'distance_km': float(house.distance_km),
                       'price_usd': float(house.price), 'price_vnd': float(house.price * rate),
                       'price_per_m2_vnd': float(house.price * rate / house.living_m2)})
    return answer


def estimate_property(payload, model_path=MODEL):
    bundle = load_bundle(model_path)
    meta, model = bundle['metadata'], bundle['model']
    row = validate_property(payload, meta)
    columns = meta['features']
    predicted = float(model.predict(row[columns])[0])
    if not np.isfinite(predicted) or predicted <= 0:
        raise ValueError('Mô hình trả giá không hợp lệ.')
    rate = float(meta['exchange_rate']['usd_vnd'])
    radius = meta['calibration']['log_radius']
    low, high = max(0, np.expm1(np.log1p(predicted) - radius)), np.expm1(np.log1p(predicted) + radius)
    explanation = contributions(model, row, columns)
    effects, base_usd = [], None
    if explanation is not None:
        values, base = explanation
        base_usd = float(np.expm1(base[0]))
        effects = [{'feature': key, 'label': LABELS[key], 'log_contribution': float(value),
                    'factor': float(np.exp(value))}
                   for key, value in values.iloc[0].items()]
        effects.sort(key=lambda item: abs(item['log_contribution']), reverse=True)
    support_distance, _ = BallTree(np.radians(bundle['reference'][['latitude', 'longitude']]), metric='haversine').query(
        np.radians(row[['latitude', 'longitude']]), k=1)
    warnings = [LIMITATION,
                'Khoảng dự đoán 90% là mức danh nghĩa. Độ phủ thực tế trên test: '
                + f"{meta['test_metrics']['interval_coverage'] * 100:.1f}%.",
                'Khoảng cách là đường chim bay tới đối tượng được ghi trên OSM ngày 01/05/2014. OSM có thể thiếu địa điểm.']
    if support_distance[0, 0] * EARTH_KM > 5:
        warnings.append('Căn nhà cách mẫu huấn luyện gần nhất hơn 5 km. Kết quả có thể kém tin cậy.')
    if row.living_m2.iloc[0] < meta['living_p01'] or row.living_m2.iloc[0] > meta['living_p99']:
        warnings.append('Diện tích thuộc nhóm 1% nhỏ nhất hoặc lớn nhất của tập huấn luyện.')
    return {'predicted_vnd': predicted * rate, 'predicted_usd': predicted,
            'price_per_m2_vnd': predicted * rate / row.living_m2.iloc[0],
            'interval_vnd': [float(low * rate), float(high * rate)],
            'exchange_rate': meta['exchange_rate'], 'model_version': meta['model_version'],
            'explanations': effects, 'base_price_usd': base_usd,
            'explanation_unit': 'log1p(USD); đóng góp mô hình, không phải quan hệ nhân quả',
            'amenities': nearest_amenities(row),
            'amenities_used_by_model': any(key in columns for key in POI_FEATURES),
            'comparables': comparable_sales(row, bundle['reference'], rate, payload.get('id')),
            'warnings': warnings, 'market': 'King County, Washington, USA',
            'sale_date': row.sale_date.iloc[0]}
