"""Pinned Kaggle 2024 source, conservative address parsing and grouped holdouts."""
from pathlib import Path
import hashlib
import json
import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from .config import ROOT

RAW = ROOT / 'data/raw/kaggle_vietnam_2024'
SOURCE_URL = 'https://www.kaggle.com/datasets/nguyentiennhan/vietnam-housing-dataset-2024'
CITIES = ['Hồ Chí Minh', 'Hà Nội']
NUMERIC_MAP = {'Area':'area', 'Bedrooms':'bedroom_count', 'Bathrooms':'bathroom_count',
               'Floors':'floor_count', 'Frontage':'frontage_width', 'Access Road':'road_width'}
CATEGORY_MAP = {'House direction':'house_direction', 'Legal status':'legal_status',
                'Furniture state':'furniture_state'}
NUMERIC = list(NUMERIC_MAP.values())
CATEGORICAL = ['province_name','district_name','ward_name'] + list(CATEGORY_MAP.values())
FEATURES = NUMERIC + CATEGORICAL
LIMITS = {'area':(15,1000),'bedroom_count':(1,20),'bathroom_count':(1,20),
          'floor_count':(1,15),'frontage_width':(1,50),'road_width':(1,60)}
OPTIONAL_CATEGORIES = {'house_direction': ['Bắc','Đông - Bắc','Đông','Đông - Nam','Nam','Tây - Nam','Tây','Tây - Bắc'],
    'legal_status':['Have certificate','Sale contract'], 'furniture_state':['Full','Basic']}
LABELS = {'area':'Diện tích','bedroom_count':'Phòng ngủ','bathroom_count':'Phòng tắm',
    'floor_count':'Số tầng','frontage_width':'Mặt tiền','road_width':'Đường trước nhà',
    'province_name':'Thành phố','district_name':'Quận/huyện','ward_name':'Phường/xã',
    'house_direction':'Hướng nhà','legal_status':'Pháp lý','furniture_state':'Nội thất'}
SCOPE = ('Giá rao bán tham khảo tại TP.HCM và Hà Nội, học từ House Price Prediction Dataset Vietnam 2024 '
         'của Nguyen Tien Nhan trên Kaggle, phiên bản 8. Giá nguồn theo tỷ VND được đổi sang VND. '
         'Không có ngày đăng từng tin; kết quả kiểm thử là chia ngẫu nhiên theo nhóm, chưa phải dự báo theo thời gian. '
         'Tên địa bàn theo địa chỉ nguồn; chưa xác minh giá chốt giao dịch hoặc giá hiện tại.')


def text(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(value))).strip().rstrip('.').strip()


def parse_address(address):
    pieces = [text(x) for x in str(address).split(',') if text(x)]
    if len(pieces) < 2:
        return None, None, 'Không rõ'
    aliases = {'TP. HCM':'Hồ Chí Minh','TP HCM':'Hồ Chí Minh','TPHCM':'Hồ Chí Minh',
               'TpHCM':'Hồ Chí Minh','TP Hồ Chí Minh':'Hồ Chí Minh','HN':'Hà Nội'}
    city = aliases.get(pieces[-1], pieces[-1])
    district = re.sub(r'^(Huyện|Thành phố|Thị xã)\s+', '', pieces[-2], flags=re.I)
    # Keep Quận 1 .. Quận 12, but reconcile Quận Long Biên / Long Biên.
    district = re.sub(r'^Quận\s+(?=\D)', '', district, flags=re.I)
    if re.match(r'^(Phường|Xã|Thị trấn)\b', district, re.I):
        district = None
    ward = pieces[-3] if len(pieces) >= 3 and re.match(r'^(Phường|Xã|Thị trấn)\b', pieces[-3], re.I) else 'Không rõ'
    return city, district, ward


def prepare_listings(raw_dir=RAW):
    raw_dir = Path(raw_dir)
    manifest = json.loads((raw_dir/'manifest.json').read_text(encoding='utf-8'))
    item = manifest['files'][0]
    path = raw_dir/item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('Checksum CSV Kaggle không khớp.')
    raw = pd.read_csv(path)
    if list(raw.columns) != manifest['columns']:
        raise ValueError('Schema Kaggle thay đổi; cần kiểm tra ánh xạ.')
    locations = pd.DataFrame([parse_address(x) for x in raw.Address], columns=['province_name','district_name','ward_name'])
    data = raw.rename(columns=NUMERIC_MAP | CATEGORY_MAP).join(locations)
    data['source_row'] = np.arange(len(data))
    audit = {'raw_rows':len(raw), 'raw_columns':len(raw.columns), 'files':1}
    data = data[data.province_name.isin(CITIES)].copy()
    audit['in_scope_rows'] = len(data)
    for name in NUMERIC:
        data[name] = pd.to_numeric(data[name],errors='coerce')
    data['price'] = pd.to_numeric(data.Price,errors='coerce') * 1e9
    valid = (data.price.between(.5e9,200e9) & data.area.between(*LIMITS['area'])
             & (data.price/data.area).between(5e6,800e6) & data.district_name.notna())
    audit['invalid_or_outside_price_scope'] = int((~valid).sum())
    data = data[valid].copy()
    audit['optional_values_set_missing'] = {}
    for name in NUMERIC[1:]:
        invalid = data[name].notna() & (~data[name].between(*LIMITS[name]))
        if name.endswith('_count'):
            invalid |= data[name].notna() & (data[name]%1 != 0)
        audit['optional_values_set_missing'][name] = int(invalid.sum())
        data.loc[invalid,name] = np.nan
    for name in CATEGORICAL:
        data[name] = data[name].fillna('Không rõ').map(text)
    before = len(data)
    data = data.drop_duplicates(subset=[NUMERIC_MAP.get(c,CATEGORY_MAP.get(c,c)) for c in raw.columns])
    audit['exact_duplicate_rows_removed'] = before-len(data)
    # Price and optional fields are excluded from the proxy to group reposts
    # even when the stated price or structural attributes differ.
    address = data.Address.map(lambda value: text(value).casefold())
    key = address + '|' + data.area.round(1).astype(str)
    data['group_id'] = key.map(lambda value: hashlib.sha256(value.encode('utf-8')).hexdigest()[:24])
    data['listing_id'] = data.source_row.map(lambda row: hashlib.sha256((item['sha256']+':'+str(row)).encode()).hexdigest()[:24])
    data['published_at'] = None
    data['balcony_direction'] = data['Balcony direction']
    data['address'] = data.Address
    # Compatibility field for the observed catalog; it is never a model input.
    data['property_type_name'] = 'Nguồn không phân loại'
    audit['accepted_rows'] = len(data)
    audit['property_proxy_groups'] = int(data.group_id.nunique())
    audit['rows_sharing_proxy'] = int(data.group_id.duplicated().sum())
    audit['missing_fraction'] = {name:float(data[name].isna().mean()) for name in NUMERIC}
    audit['observed_price_billion_range'] = [float(data.price.min()/1e9),float(data.price.max()/1e9)]
    audit['deduplication'] = ('Bỏ dòng trùng toàn bộ 12 cột. Khóa nhóm là địa chỉ chuẩn hóa và diện tích làm tròn 0,1 m², '
        'không dùng giá. Các tin cùng khóa được giữ cùng một tập; có thể gộp nhiều căn cùng địa chỉ/diện tích và bỏ sót tin đăng lại đổi cách ghi.')
    return data.reset_index(drop=True), audit, manifest


def grouped_split(data):
    def take(frame, proportion, seed):
        a,b = next(GroupShuffleSplit(n_splits=1,test_size=proportion,random_state=seed).split(frame,groups=frame.group_id))
        return frame.iloc[a].copy(),frame.iloc[b].copy()
    rest,test = take(data,.15,42)
    rest,calibration = take(rest,.10/.85,43)
    train,validation = take(rest,.15/.75,44)
    parts = {'train':train,'validation':validation,'calibration':calibration,'test':test}
    groups = [set(part.group_id) for part in parts.values()]
    if any(groups[i]&groups[j] for i in range(4) for j in range(i+1,4)):
        raise AssertionError('Một khóa nhóm xuất hiện trong hai tập.')
    if any(len(part)<100 for part in parts.values()):
        raise ValueError('Chưa đủ quan sát cho bốn tập.')
    return parts
