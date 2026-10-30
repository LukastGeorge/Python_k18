"""Temporal model selection and property-disjoint evaluation for public US sales."""
import hashlib
import json
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from src.us_housing import ROOT, DB, ARTIFACTS, NUMERIC, CATEGORICAL, FEATURES, read_sales, temporal_split, LIMITATION


def pipeline(estimator):
    transform = ColumnTransformer([
        ('number', StandardScaler(), NUMERIC),
        ('category', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL),
    ])
    return TransformedTargetRegressor(
        regressor=Pipeline([('prepare', transform), ('regressor', estimator)]),
        func=np.log1p, inverse_func=np.expm1)


def score(actual, predicted):
    return {'mae': float(mean_absolute_error(actual, predicted)),
            'rmse': float(root_mean_squared_error(actual, predicted)),
            'r2': float(r2_score(actual, predicted))}


def main():
    data = read_sales()
    train, validation, test = temporal_split(data)
    candidates = {
        'Median baseline': DummyRegressor(strategy='median'),
        'Ridge regression': Ridge(alpha=10),
        'Random Forest': RandomForestRegressor(n_estimators=140, min_samples_leaf=4, max_depth=20, n_jobs=2, random_state=42),
        'Histogram Gradient Boosting': HistGradientBoostingRegressor(max_iter=220, max_leaf_nodes=23,
             l2_regularization=5, learning_rate=0.06, early_stopping=False, random_state=42),
    }
    results = []
    for name, estimator in candidates.items():
        model = pipeline(estimator).fit(train[FEATURES], train.price_usd)
        results.append({'model': name, **score(validation.price_usd, model.predict(validation[FEATURES]))})
        print(name, results[-1], flush=True)
    scores = pd.DataFrame(results).sort_values('rmse')
    selected = scores.iloc[0].model
    scores.to_csv(ARTIFACTS / 'validation_metrics.csv', index=False)
    evaluation_train = pd.concat([train, validation], ignore_index=True)
    evaluation_model = pipeline(clone(candidates[selected])).fit(evaluation_train[FEATURES], evaluation_train.price_usd)
    predicted = evaluation_model.predict(test[FEATURES])
    test_metrics = score(test.price_usd, predicted)
    test_results = test[['transaction_id', 'property_id', 'state', 'sale_date', 'price_usd']].copy()
    test_results['predicted_usd'] = predicted
    test_results.to_csv(ARTIFACTS / 'test_predictions.csv', index=False)
    joblib.dump(evaluation_model, ARTIFACTS / 'evaluation_model.joblib', compress=3)
    # This separate serving model uses all accepted observations including recent sales.
    serving_model = pipeline(clone(candidates[selected])).fit(data[FEATURES], data.price_usd)
    joblib.dump(serving_model, ARTIFACTS / 'model.joblib', compress=3)
    scopes = {}
    for (state, locality), group in data.groupby(['state', 'locality']):
        if len(group) < 100 or len(test[(test.state == state) & (test.locality == locality)]) < 30:
            continue
        area_types = group.area_kind.unique()
        if len(area_types) != 1:
            raise ValueError('Ambiguous area definition in a locality.')
        scopes[state + '|' + locality] = {
            'state': state, 'locality': locality, 'area_kind': area_types[0], 'rows': len(group),
            'first_date': group.sale_date.min(), 'last_date': group.sale_date.max(),
            'bounds': {c: [float(group[c].min()), float(group[c].max())]
                       for c in ['area_sqft', 'bedrooms', 'bathrooms', 'year_built']},
            'defaults': {c: float(group[c].median()) for c in NUMERIC},
        }
    by_state = {state: score(g.price_usd, g.predicted_usd) for state, g in test_results.groupby('state')}
    metadata = {
        'created_at': datetime.now(timezone.utc).isoformat(), 'selected_model': selected,
        'database_sha256': hashlib.sha256(DB.read_bytes()).hexdigest(), 'features': FEATURES,
        'rows': len(data), 'train_rows': len(train), 'validation_rows': len(validation), 'test_rows': len(test),
        'purged_rows': len(data) - len(train) - len(validation) - len(test),
        'split_policy': 'Train 2016–2023; validation 2024; test 2025–2026. Purge earlier sales of holdout properties.',
        'selection': 'Lowest validation RMSE; no selection from test.',
        'evaluation_model': 'Refit selected model on train + validation; test properties excluded.',
        'serving_model': 'Separate final refit on all valid records 2016–2026. Test scores belong to evaluation_model only.',
        'test_metrics': test_metrics, 'test_metrics_by_state': by_state, 'scopes': scopes,
        'limitation': LIMITATION,
    }
    (ARTIFACTS / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    split = {name: group.transaction_id.tolist() for name, group in [('train', train), ('validation', validation), ('test', test)]}
    (ARTIFACTS / 'split.json').write_text(json.dumps(split), encoding='utf-8')
    data.groupby('state').tail(3)[FEATURES].to_csv(ROOT / 'data/us_sample_input.csv', index=False)
    print('Selected:', selected, 'test:', test_metrics, 'rows:', len(data), flush=True)


if __name__ == '__main__':
    main()
