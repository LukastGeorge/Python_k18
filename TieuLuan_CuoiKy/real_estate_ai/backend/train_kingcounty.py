"""Reproducible four-block King County experiment and serving artifact."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from .config import configure_console, get_engine
from .kingcounty import (RAW, CONTEXT, ARTIFACTS, MODEL, BASE_FEATURES, HOUSE_FEATURES,
                         POI_FEATURES, LABELS, LIMITATION, EXPECTED_SHA, prepare_sales,
                         temporal_partitions, read_fx, contributions, points_of_interest,
                         sha256, estimate_property)


def make_pipeline(estimator, features):
    categories = [key for key in features if key == 'zipcode']
    numbers = [key for key in features if key not in categories]
    transforms = [('numeric', Pipeline([('impute', SimpleImputer(strategy='median')),
                                        ('scale', StandardScaler())]), numbers)]
    if categories:
        transforms.append(('category', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categories))
    return TransformedTargetRegressor(regressor=Pipeline([
        ('prepare', ColumnTransformer(transforms)), ('regressor', estimator)]),
        func=np.log1p, inverse_func=np.expm1)


def metrics(actual, predicted):
    a, p = np.asarray(actual), np.asarray(predicted)
    if not np.isfinite(p).all() or (p <= 0).any():
        raise ValueError('Dự đoán chứa giá không hữu hạn hoặc không dương.')
    ape = np.abs(a - p) / a
    return {'mae_usd': float(mean_absolute_error(a, p)),
            'rmse_usd': float(root_mean_squared_error(a, p)), 'r2': float(r2_score(a, p)),
            'median_ape': float(np.median(ape)), 'mape': float(np.mean(ape)),
            'within_10pct': float(np.mean(ape <= .1)), 'within_20pct': float(np.mean(ape <= .2))}


def quality_gate(candidate, baseline):
    if (not np.isfinite(list(candidate.values())).all() or candidate['r2'] <= 0
            or candidate['rmse_usd'] >= baseline['rmse_usd']
            or candidate['mae_usd'] >= baseline['mae_usd']):
        raise ValueError('Mô hình không vượt baseline trên validation; giữ mô hình hiện có.')


def input_of(house):
    keys = ['living_m2', 'lot_m2', 'bedrooms', 'bathrooms', 'floors', 'waterfront',
            'view', 'condition', 'grade', 'latitude', 'longitude']
    result = {key: float(house[key]) for key in keys}
    result.update(zipcode=str(house.zipcode), year_built=int(house.yr_built),
                  year_renovated=int(house.yr_renovated), sale_date=house.sale_date.strftime('%Y-%m-%d'), id=str(house.id))
    return result


def import_database(data, rate, engine):
    """A separate transaction table preserves all existing user-entered records."""
    from sqlalchemy import MetaData, Table, Column, String, Float, Text
    from sqlalchemy.dialects.sqlite import insert as si
    from sqlalchemy.dialects.postgresql import insert as pi
    table = Table('kingcounty_sales', MetaData(),
                  Column('transaction_id', String(180), primary_key=True),
                  Column('property_id', String(160), nullable=False),
                  Column('sale_date', String(10), nullable=False),
                  Column('price_usd', Float, nullable=False),
                  Column('price_vnd', Float, nullable=False),
                  Column('usd_vnd', Float, nullable=False),
                  Column('features_json', Text, nullable=False))
    table.metadata.create_all(engine)
    insert = {'sqlite': si, 'postgresql': pi}[engine.dialect.name]
    rows = [{'transaction_id': r.transaction_id, 'property_id': r.id,
             'sale_date': r.sale_date.strftime('%Y-%m-%d'), 'price_usd': float(r.price),
             'price_vnd': float(r.price * rate), 'usd_vnd': rate,
             'features_json': json.dumps(input_of(r), ensure_ascii=False)} for _, r in data.iterrows()]
    with engine.begin() as con:
        for start in range(0, len(rows), 100):
            stmt = insert(table).values(rows[start:start + 100])
            stmt = stmt.on_conflict_do_update(index_elements=['transaction_id'],
                      set_={c.name: getattr(stmt.excluded, c.name) for c in table.c if not c.primary_key})
            con.execute(stmt)
    return len(rows)


def train(*, import_db=False, model_path=MODEL):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    data, audit = prepare_sales()
    parts = temporal_partitions(data)
    train, val, cal, test = (parts[key] for key in ['train', 'validation', 'calibration', 'test'])
    fx = read_fx()
    has_poi = data[POI_FEATURES].notna().all().all()
    xgb = XGBRegressor(n_estimators=450, max_depth=5, learning_rate=.035, subsample=.9,
                       colsample_bytree=.9, reg_lambda=5, objective='reg:squarederror',
                       tree_method='hist', n_jobs=2, random_state=42)
    candidates = {
        'Median baseline': (DummyRegressor(strategy='median'), BASE_FEATURES),
        'Ridge 4 biến': (Ridge(alpha=10), BASE_FEATURES),
        'XGBoost 4 biến': (clone(xgb), BASE_FEATURES),
        'XGBoost nhà và vị trí': (clone(xgb), HOUSE_FEATURES),
    }
    if has_poi:
        candidates['XGBoost thêm tiện ích OSM'] = (clone(xgb), HOUSE_FEATURES + POI_FEATURES)
    scores = []
    for name, (estimator, cols) in candidates.items():
        model = make_pipeline(estimator, cols).fit(train[cols], train.price)
        score = {'model': name, **metrics(val.price, model.predict(val[cols]))}
        scores.append(score)
        print('VALIDATION', name, score, flush=True)
    scores = pd.DataFrame(scores).sort_values('rmse_usd')
    selected = scores.iloc[0]['model']
    val_score = scores.iloc[0].drop('model').to_dict()
    baseline_score = scores.loc[scores.model == 'Median baseline'].iloc[0].drop('model').to_dict()
    quality_gate(val_score, baseline_score)
    estimator, cols = candidates[selected]
    reference = pd.concat([train, val], ignore_index=True)
    model = make_pipeline(clone(estimator), cols).fit(reference[cols], reference.price)
    residuals = np.abs(np.log1p(cal.price.to_numpy()) - np.log1p(model.predict(cal[cols])))
    quantile = min(1, np.ceil((len(cal) + 1) * .9) / len(cal))
    radius = float(np.quantile(residuals, quantile, method='higher'))
    predicted = model.predict(test[cols])
    lo = np.maximum(0, np.expm1(np.log1p(predicted) - radius))
    hi = np.expm1(np.log1p(predicted) + radius)
    test_score = metrics(test.price, predicted)
    test_score['interval_coverage'] = float(np.mean((test.price >= lo) & (test.price <= hi)))
    test_score['median_interval_width_usd'] = float(np.median(hi - lo))
    baseline = make_pipeline(DummyRegressor(strategy='median'), BASE_FEATURES).fit(reference[BASE_FEATURES], reference.price)
    baseline_test = metrics(test.price, baseline.predict(test[BASE_FEATURES]))
    defaults = input_of(reference.iloc[(reference.price - reference.price.median()).abs().argmin()])
    for key in ['id', 'sale_date']:
        defaults.pop(key)
    defaults['year_renovated'] = 0
    bounds = {}
    source_names = {'year_built': 'yr_built', 'year_renovated': 'yr_renovated'}
    for key in defaults:
        if key != 'zipcode':
            source = data[source_names.get(key, key)]
            bounds[key] = [float(source.min()), float(source.max())]
    # Domain bounds only validate input. All fitted transforms and models use train blocks only.
    # An old model is replaced only if its recorded validation design is directly comparable.
    model_path = Path(model_path)
    if model_path.exists():
        previous = joblib.load(model_path)['metadata']
        if previous.get('dataset_sha256') == EXPECTED_SHA and previous.get('split_version') == 'four-block-v1':
            if val_score['rmse_usd'] > previous['validation_metrics']['rmse_usd'] * 1.01:
                raise ValueError('RMSE validation xấu hơn mô hình hiện tại trên cùng phép chia. Giữ bản cũ.')
    splits = {name: {'rows': len(group), 'houses': int(group.id.nunique()),
                     'first_date': group.sale_date.min().strftime('%Y-%m-%d'),
                     'last_date': group.sale_date.max().strftime('%Y-%m-%d')}
              for name, group in parts.items()}
    metadata = {'schema': 'kingcounty-v1', 'model_version': datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
                'selected_model': selected, 'features': cols, 'dataset_sha256': EXPECTED_SHA,
                'dataset_source': 'https://www.kaggle.com/datasets/harlfoxem/housesalesprediction',
                'split_version': 'four-block-v1', 'splits': splits,
                'purged_rows': len(data) - sum(len(g) for g in parts.values()),
                'selection': 'Lowest validation RMSE only. Test never selects features or hyperparameters.',
                'serving_policy': 'Serving model is the evaluated train+validation model; calibration and test never fitted.',
                'validation_metrics': val_score, 'test_metrics': test_score, 'baseline_test_metrics': baseline_test,
                'exchange_rate': fx, 'target_currency': 'USD', 'display_currency': 'VND',
                'calibration': {'nominal_coverage': .9, 'log_radius': radius, 'rows': len(cal),
                                'method': 'Split conformal absolute log residual, finite-sample higher quantile. Temporal shift can reduce coverage.'},
                'first_date': '2014-05-02', 'last_date': '2015-05-27', 'audit': audit,
                'input_defaults': defaults, 'input_bounds': bounds, 'zipcodes': sorted(data.zipcode.unique().tolist()),
                'living_p01': float(reference.living_m2.quantile(.01)), 'living_p99': float(reference.living_m2.quantile(.99)),
                'poi_available': bool(has_poi), 'poi_counts': points_of_interest().kind.value_counts().to_dict(),
                'poi_snapshot': '2014-05-01T00:00:00Z' if has_poi else None,
                'limitation': LIMITATION,
                'excluded_features': ['price_per_m2 (derived from target)', 'id (identifier)',
                                      'sqft_living15/sqft_lot15 (historical vintage not verified)']}
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=model_path.parent, suffix='.tmp', delete=False) as f:
        temporary = Path(f.name)
    try:
        joblib.dump({'schema': 'kingcounty-v1', 'model': model, 'metadata': metadata,
                     'reference': reference}, temporary, compress=3)
        os.replace(temporary, model_path)
    finally:
        temporary.unlink(missing_ok=True)
    scores.to_csv(ARTIFACTS / 'validation_metrics.csv', index=False)
    result = test[['transaction_id', 'id', 'sale_date', 'price', 'living_m2', 'zipcode', 'bedrooms', 'bathrooms']].copy()
    result['predicted_usd'], result['lower_usd'], result['upper_usd'] = predicted, lo, hi
    result['absolute_error_usd'] = np.abs(result.price - predicted)
    result['ape'] = result.absolute_error_usd / result.price
    result.to_csv(ARTIFACTS / 'test_predictions.csv', index=False)
    data.to_csv(ARTIFACTS / 'sales_clean.csv', index=False)
    (ARTIFACTS / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    (ARTIFACTS / 'split.json').write_text(json.dumps({k: g.transaction_id.tolist() for k, g in parts.items()}), encoding='utf-8')
    explanations = contributions(model, val.iloc[:1000], cols)
    if explanations:
        global_importance = explanations[0].abs().mean().sort_values(ascending=False)
        global_importance.rename('mean_abs_log_shap').to_csv(ARTIFACTS / 'feature_importance.csv')
    # Fixed median-price held-out case plus two fixed test records, selected without looking at errors.
    example_rows = [test.iloc[(test.price - test.price.median()).abs().argmin()], test.iloc[0], test.iloc[len(test) // 2]]
    examples = []
    for number, house in enumerate(example_rows):
        payload = input_of(house)
        examples.append({'name': 'Căn nhà test ' + str(number + 1), 'input': payload,
                         'actual_usd': float(house.price), 'actual_vnd': float(house.price * fx['usd_vnd']),
                         'result': estimate_property(payload, model_path)})
    (ARTIFACTS / 'examples.json').write_text(json.dumps(examples, ensure_ascii=False, indent=2), encoding='utf-8')
    if import_db:
        engine = get_engine()
        try:
            print('IMPORTED', import_database(data, fx['usd_vnd'], engine), flush=True)
        finally:
            engine.dispose()
    print('SELECTED', selected, 'TEST', test_score, 'SPLITS', splits, flush=True)
    return metadata


def main():
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--import-db', action='store_true', help='UPSERT dataset vào bảng kingcounty_sales riêng.')
    args = parser.parse_args()
    train(import_db=args.import_db)


if __name__ == '__main__':
    main()
