"""Train the pinned Kaggle 2024 source with disjoint property-proxy groups."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .vietnam import (ARTIFACTS, RAW, FEATURES, NUMERIC, CATEGORICAL, SCOPE,
    prepare_listings, grouped_split, build_regressor, fit_baseline, predict_baseline,
    normalize_features, contributions, json_write)


def metrics(actual, predicted):
    actual, predicted = np.asarray(actual, float), np.asarray(predicted, float)
    ape = np.abs(predicted - actual) / actual
    return {'n': len(actual), 'mae_vnd': float(mean_absolute_error(actual, predicted)),
            'rmse_vnd': float(np.sqrt(mean_squared_error(actual, predicted))),
            'r2': float(r2_score(actual, predicted)), 'median_ape': float(np.median(ape)),
            'within_20pct': float(np.mean(ape <= .2))}


def train(raw_dir=RAW, output=ARTIFACTS, clean_path=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if clean_path is None:
        data, audit, source = prepare_listings(raw_dir)
    else:
        clean_path = Path(clean_path)
        provenance = json.loads(clean_path.with_name('clean_manifest.json').read_text(encoding='utf-8'))
        if hashlib.sha256(clean_path.read_bytes()).hexdigest() != provenance['sha256']:
            raise ValueError('Checksum CSV Việt Nam đã làm sạch không khớp.')
        data = pd.read_csv(clean_path, dtype={'listing_id': str, 'group_id': str,
                                            'ward_name': str, 'district_name': str})
        audit, source = provenance['audit'], provenance['source']
    parts = grouped_split(data)
    fit, val, cal, test = [parts[name] for name in ['train', 'validation', 'calibration', 'test']]
    audit['training_missing_fraction'] = {name:float(fit[name].isna().mean()) for name in NUMERIC+['balcony_direction']}
    audit['training_missing_fraction'].update({name:float(fit[name].eq('Không rõ').mean())
                                              for name in CATEGORICAL})
    if audit['training_missing_fraction']['balcony_direction'] <= .8:
        raise ValueError('Hướng ban công không còn vượt ngưỡng thiếu 80%; cần xem lại quy tắc sàng lọc.')
    print('Splits', {key: len(value) for key, value in parts.items()}, flush=True)
    baseline = fit_baseline(fit)
    comparison = [{'model': 'Trung vị VND/m² theo khu vực', **metrics(val.price, predict_baseline(val, baseline))}]
    models = []
    for location in [False, True]:
        model = build_regressor(location)
        model.fit(normalize_features(fit), np.log(fit.price))
        label = 'XGBoost thêm địa bàn' if location else 'XGBoost chưa dùng địa bàn'
        score = metrics(val.price, np.exp(model.predict(normalize_features(val))))
        comparison.append({'model': label, **score})
        models.append((score['rmse_vnd'], location, label))
        print(label, score, flush=True)
    _, location, selected = min(models)
    # Selection depends only on validation. Calibration/test are never fitted.
    serving = pd.concat([fit, val], ignore_index=True)
    pipeline = build_regressor(location)
    pipeline.fit(normalize_features(serving), np.log(serving.price))
    residual = np.abs(np.log(cal.price.to_numpy()) - pipeline.predict(normalize_features(cal)))
    level = min(1., np.ceil((len(residual) + 1) * .9) / len(residual))
    quantile = float(np.quantile(residual, level, method='higher'))
    log_hat = pipeline.predict(normalize_features(test)).astype(float)
    predicted = np.exp(log_hat)
    scores = metrics(test.price, predicted)
    low, high = np.exp(log_hat - quantile), np.exp(log_hat + quantile)
    scores['coverage_90'] = float(np.mean((test.price >= low) & (test.price <= high)))
    scores['median_interval_width_vnd'] = float(np.median(high - low))
    baseline_test = metrics(test.price, predict_baseline(test, fit_baseline(serving)))
    if scores['rmse_vnd'] >= baseline_test['rmse_vnd'] or scores['r2'] <= 0:
        raise ValueError('Mô hình chưa vượt baseline trên test; giữ nguyên mô hình đang phục vụ.')
    splits = {name: {'n': len(part), 'groups':int(part.group_id.nunique()),
                     'first_date':None,'last_date':None}
              for name, part in parts.items()}
    locations = {}
    for (city, district), group in serving.groupby(['province_name', 'district_name']):
        if len(group)>=20:
            locations.setdefault(city, {})[district] = {'wards': sorted(set(group.ward_name) - {'Không rõ'}), 'n': len(group)}
    area_ranges = {city: [float(group.area.quantile(.01)), float(group.area.quantile(.99))]
                   for city, group in serving.groupby('province_name')}
    version = 'vn2024-' + hashlib.sha256((source['revision'] + json.dumps(scores, sort_keys=True)).encode()).hexdigest()[:12]
    meta = {'model_version': version, 'created_at': datetime.now(timezone.utc).isoformat(),
        'target': 'asking_price_vnd', 'currency': 'VND', 'scope': SCOPE, 'selected_model': selected,
        'features': FEATURES, 'source': source, 'audit': audit, 'splits': splits,
        'validation_comparison': comparison, 'test': scores, 'baseline_test': baseline_test,
        'locations': locations, 'area_ranges': area_ranges,
        'split_method':'GroupShuffleSplit by normalized Address + rounded Area; 60/15/10/15 percent of proxy groups; seeds 42/43/44.',
        'time_validation':False, 'property_types_available':False,
        'calibration': {'nominal_coverage': .9, 'q_log_vnd': quantile, 'method': 'split conformal absolute log residual'},
        'amenities_available': False,
        'limitations': ['Nguồn Kaggle phiên bản 8 năm 2024; không đại diện toàn bộ thị trường.',
            'Price là giá rao theo tỷ VND, được nhân 1.000.000.000; chưa xác minh giao dịch.',
            'Không có ngày đăng từng tin; chia ngẫu nhiên theo nhóm, chưa đánh giá dự báo ở thời kỳ tương lai.',
            'Không có cột loại nhà; không tự gán nhãn nhà riêng, căn hộ hoặc biệt thự.',
            'Chưa có mã nhà độc lập; nhóm địa chỉ và diện tích có thể gộp nhầm căn khác hoặc bỏ sót tin đăng lại.',
            'Không có tọa độ/POI xác minh; không suy diễn gần trường/cửa hàng từ lời quảng cáo.',
            'Dữ liệu giữ lại có giá 1–11,5 tỷ VND; không suy rộng chất lượng sang phân khúc giá cao hơn.',
            'Diện tích theo tin đăng có thể là diện tích đất hoặc sàn; đơn giá chỉ dùng diện tích khai báo.',
            'Giới hạn giá 0,5–200 tỷ, diện tích 15–1.000m², đơn giá 5–800 triệu/m².',
            'Khoảng 90% không bảo đảm độ phủ khi chuyển thời kỳ hoặc phân khúc.']}
    breakdown = []
    for dimension in ['province_name']:
        for label, group in test.groupby(dimension):
            indexes = test.index.get_indexer(group.index)
            values = metrics(group.price, predicted[indexes])
            values['coverage_90'] = float(np.mean((group.price >= low[indexes]) & (group.price <= high[indexes])))
            breakdown.append({'dimension': dimension, 'label': label, **values})
    meta['test_breakdown'] = breakdown
    comparison_cols = ['listing_id', 'group_id', 'published_at', 'price'] + FEATURES
    bundle = {'pipeline': pipeline, 'metadata': meta, 'calibration_q': quantile,
              'comparables': serving[comparison_cols].copy()}
    temporary = output / 'model.pending.joblib'
    joblib.dump(bundle, temporary, compress=3)
    temporary.replace(output / 'model.joblib')
    json_write(output / 'metadata.json', meta)
    json_write(output / 'split.json', {name: part.listing_id.tolist() for name, part in parts.items()})
    test_results = test[comparison_cols].copy()
    test_results['predicted_vnd'] = predicted
    test_results['lower_90_vnd'], test_results['upper_90_vnd'] = low, high
    test_results.to_csv(output / 'test_predictions.csv', index=False)
    # Compact, source-attributed CSV lets a fresh checkout retrain without the 164MB shard.
    data[comparison_cols+['address','property_type_name','balcony_direction']].to_csv(output / 'listings_clean.csv.gz', index=False, compression='gzip')
    json_write(output / 'clean_manifest.json', {'source': source, 'audit': audit,
        'sha256': hashlib.sha256((output / 'listings_clean.csv.gz').read_bytes()).hexdigest(),
        'description': 'Tập con TP.HCM và Hà Nội từ Kaggle 2024 phiên bản 8, giấy phép CC0; checksum dữ liệu gốc và dữ liệu sạch được ghi riêng.'})
    sample = cal.sample(min(600, len(cal)), random_state=42)
    effects, _ = contributions(pipeline, sample)
    json_write(output / 'importance.json', [{'feature': feature, 'mean_abs_log_contribution': float(value)}
        for feature, value in zip(FEATURES, np.abs(effects).mean(axis=0))])
    examples = []
    for city, group in test.groupby('province_name'):
        # Deterministic median-price example, independent of its prediction error.
        complete = group.dropna(subset=['bedroom_count', 'bathroom_count'])
        if len(complete) >= 10:
            group = complete
        group = group[group.district_name.isin(locations[city])]
        row = group.iloc[np.argsort(group.price.to_numpy())[len(group) // 2]]
        values = {name: None if pd.isna(row[name]) else row[name] for name in FEATURES}
        if values['ward_name'] not in locations[city][row.district_name]['wards']:
            values['ward_name'] = 'Không rõ'
        examples.append({'label': f'{city} · {row.district_name}', 'input': values | {'reference_id': row.listing_id},
                         'asking_vnd': float(row.price), 'published_at':None})
    json_write(output / 'examples.json', examples)
    print('SELECTED', selected, 'TEST', scores, 'BASELINE', baseline_test, flush=True)
    return meta


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=RAW)
    parser.add_argument('--output', type=Path, default=ARTIFACTS)
    parser.add_argument('--clean', type=Path, help='CSV gzip đã xác minh cùng clean_manifest.json')
    parser.add_argument('--import-db', action='store_true', help='Nhập tin nguồn vào database đang cấu hình')
    args = parser.parse_args()
    train(args.raw_dir, args.output, args.clean)
    if args.import_db:
        from .import_vietnam_data import import_catalog
        from .config import get_engine
        print('Tin nguồn trong database:', import_catalog(get_engine(), args.output / 'listings_clean.csv.gz'))
