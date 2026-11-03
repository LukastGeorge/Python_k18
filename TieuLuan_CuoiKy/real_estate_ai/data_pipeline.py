"""Chạy demo hai tin mẫu hoặc nhập CSV thật; không giả vờ cào web."""
import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from config import get_engine, MODEL_PATH, configure_console
from database import save_records
from model_inference import RealEstateAI
from validation import validate_features


def scrape_hourly_news():
    """Giữ tên hàm cũ; hiện chỉ trả hai tin demo, chưa nối website thật."""
    return pd.DataFrame([
        {'id': 'news_001', 'title': '[DEMO] Nhà 50 m², 2 phòng ngủ', 'area': '50m2', 'rooms': 2,
         'latitude': 10.762622, 'longitude': 106.660172},
        {'id': 'news_002', 'title': '[DEMO] Căn hộ 75 m², 3 phòng ngủ', 'area': '75 m²', 'rooms': 3,
         'latitude': 10.762622, 'longitude': 106.660172},
    ])


def clean_data(df, *, is_demo=False, source='csv'):
    if df.empty:
        return pd.DataFrame()
    required = {'id', 'title', 'area', 'rooms', 'latitude', 'longitude'}
    if df.columns.duplicated().any() or not required.issubset(df.columns):
        raise ValueError('Dữ liệu thiếu cột bắt buộc hoặc trùng tên cột: ' + ', '.join(sorted(required)))
    df = df.copy()
    for column in ['id', 'title']:
        if df[column].isna().any() or df[column].astype(str).str.strip().eq('').any():
            raise ValueError(f'{column} không được để trống.')
        df[column] = df[column].astype(str).str.strip()
    if df.id.str.len().gt(160).any() or df.title.str.len().gt(1000).any():
        raise ValueError('ID tối đa 160 ký tự; tiêu đề tối đa 1.000 ký tự.')
    # Chấp nhận 50, 50m2, 75 m² và số thập phân dùng dấu phẩy.
    area = (df.area.astype(str).str.strip().str.lower()
            .str.replace(r'\s*m(?:2|²)\s*$', '', regex=True)
            .str.replace(',', '.', regex=False).str.strip())
    df['dien_tich'] = pd.to_numeric(area, errors='coerce')
    df['so_phong_ngu'] = pd.to_numeric(df.rooms, errors='coerce')
    features = validate_features(df)
    for column in features.columns:
        df[column] = features[column]
    if 'actual_price' not in df:
        df['actual_price'] = np.nan
    original_price = df.actual_price
    price = pd.to_numeric(original_price, errors='coerce')
    if ((original_price.notna() & price.isna()) | np.isinf(price)
            | (price.notna() & ~price.between(100_000_000, 500_000_000_000))).any():
        raise ValueError('actual_price phải là giá bán VND từ 100 triệu đến 500 tỷ, hoặc để trống.')
    df['actual_price'] = price
    if 'price_kind' not in df:
        df['price_kind'] = 'unknown'
    df['price_kind'] = df.price_kind.fillna('unknown').astype(str).str.strip().str.lower()
    if not df.price_kind.isin(['sale', 'unknown']).all():
        raise ValueError('price_kind chỉ nhận sale hoặc unknown; không nhập giá rao thành giá bán.')
    if (df.actual_price.notna() & df.price_kind.ne('sale')).any():
        raise ValueError('Khi có actual_price, cần price_kind=sale và giá phải thuộc giao dịch đã bán.')
    if not isinstance(source, str):
        raise ValueError('Tên nguồn phải là chuỗi có 1–160 ký tự.')
    source = source.strip()
    if not source or len(source) > 160:
        raise ValueError('Tên nguồn phải có 1–160 ký tự.')
    if not is_demo and source == 'demo':
        raise ValueError('Tên nguồn demo được dành riêng cho dữ liệu giả lập.')
    df['source'], df['is_demo'] = source, is_demo
    if df.id.duplicated().any():
        raise ValueError('CSV có ID trùng. Mỗi dòng phải là một căn nhà có ID ổn định trong nguồn.')
    return df[['source', 'id', 'title', 'dien_tich', 'so_phong_ngu', 'latitude', 'longitude',
               'actual_price', 'price_kind', 'is_demo']].copy()


def read_input_csv(csv_path):
    # Kiểm tra header trước khi pandas tự đổi tên cột trùng (area -> area.1).
    with Path(csv_path).open(encoding='utf-8-sig', newline='') as file:
        header = next(csv.reader(file), [])
        if len(header) != len(set(header)):
            raise ValueError('CSV trùng tên cột; mỗi cột chỉ được xuất hiện một lần.')
        file.seek(0)
        # ID như NA hoặc NULL là mã hợp lệ, không phải ô thiếu.
        return pd.read_csv(file, dtype={'id': str}, keep_default_na=False, na_values=[''])


def run_pipeline(csv_path=None, *, engine=None, model_path=MODEL_PATH, source='csv'):
    is_demo = csv_path is None
    raw = scrape_hourly_news() if is_demo else read_input_csv(csv_path)
    clean = clean_data(raw, is_demo=is_demo, source='demo' if is_demo else source)
    if clean.empty:
        print('Không có dữ liệu để xử lý.')
        return clean
    # Nạp lại ở mỗi lần chạy để nhận mô hình vừa huấn luyện, nếu có.
    ai_model = RealEstateAI(model_path, allow_demo=is_demo)
    clean['predicted_price'] = ai_model.predict_price(clean)
    clean['prediction_method'] = ai_model.method
    clean['updated_at'] = datetime.now(timezone.utc)
    owned_engine = engine is None
    db = get_engine() if owned_engine else engine
    try:
        save_records(db, clean)
    finally:
        if owned_engine:
            db.dispose()
    print(f'Đã cập nhật {len(clean)} tin trong bảng real_estate_records ({db.dialect.name}).')
    if is_demo:
        print('CHẾ ĐỘ DEMO: tin và tọa độ là mẫu giả lập, không dùng làm dữ liệu huấn luyện thật.')
    if ai_model.method == 'demo_formula':
        print('Chưa có mô hình thật; giá bên dưới tính bằng công thức minh họa.')
    elif ai_model.method == 'unavailable':
        print('Chưa có mô hình: đã lưu dữ liệu thật; predicted_price để trống. Có thể huấn luyện khi đủ mẫu.')
    print(clean[['id', 'dien_tich', 'so_phong_ngu', 'predicted_price', 'prediction_method']].to_string(index=False))
    return clean


def main(argv=None):
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, help='CSV thật; bỏ trống để chạy hai tin DEMO.')
    parser.add_argument('--source', default='csv', help='Mã nguồn ổn định để phân biệt ID của các nguồn.')
    args = parser.parse_args(argv)
    try:
        run_pipeline(args.csv, source=args.source)
    except (ValueError, OSError, SQLAlchemyError) as error:
        print(f'Không chạy được pipeline: {error}')
        print('Kiểm tra .env, database GiaNha và định dạng CSV. Xem README.md.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
