"""Huấn luyện bằng giá bán thực; dữ liệu demo và giá dự đoán bị loại."""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sqlalchemy.exc import SQLAlchemyError
from xgboost import XGBRegressor
from config import FEATURES, MODEL_PATH, get_engine, configure_console
from database import load_training_data


def load_data_from_db(engine=None):
    owned_engine = engine is None
    db = get_engine() if owned_engine else engine
    try:
        return load_training_data(db)
    finally:
        if owned_engine:
            db.dispose()


def remove_outliers(df):
    if df.empty:
        return df.copy()
    columns = FEATURES + ['actual_price']
    if not set(columns).issubset(df.columns):
        raise ValueError('Dữ liệu huấn luyện phải có đủ đặc trưng và actual_price.')
    clean = df.copy()
    clean[columns] = clean[columns].apply(pd.to_numeric, errors='coerce')
    valid = (np.isfinite(clean[columns]).all(axis=1)
        & clean.dien_tich.between(10, 1000)
        & clean.so_phong_ngu.between(0, 30) & clean.so_phong_ngu.mod(1).eq(0)
        & clean.latitude.between(-90, 90) & clean.longitude.between(-180, 180)
        & clean.actual_price.between(100_000_000, 500_000_000_000))
    return clean.loc[valid].copy()


def train_model(df, model_path=MODEL_PATH):
    clean = remove_outliers(df)
    if {'source', 'id'}.issubset(clean.columns):
        clean = clean.drop_duplicates(['source', 'id'])
    if len(clean) < 50:
        print(f'Chưa huấn luyện: chỉ có {len(clean)} mẫu giá bán thực hợp lệ; cần ít nhất 50. Mô hình hiện có được giữ lại.')
        return None
    X, y = clean[FEATURES], clean.actual_price
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6,
                         objective='reg:squarederror', tree_method='hist', n_jobs=2, random_state=42)
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    if not np.isfinite(predictions).all() or (predictions <= 0).any():
        raise ValueError('Mô hình tạo giá không hợp lệ; chưa thay thế mô hình cũ.')
    metrics = {'mae_vnd': float(mean_absolute_error(y_test, predictions)),
               'rmse_vnd': float(root_mean_squared_error(y_test, predictions)),
               'r2': float(r2_score(y_test, predictions)),
               'baseline_mae_vnd': float(mean_absolute_error(y_test, np.full(len(y_test), y_train.median()))),
               'train_rows': len(X_train), 'test_rows': len(X_test)}
    bundle = {'model': model, 'features': FEATURES, 'target': 'actual_price', 'currency': 'VND',
              'trained_at': datetime.now(timezone.utc).isoformat(), 'metrics': metrics,
              'evaluation': 'Random holdout 80/20, seed 42; saved model trained on train only.'}
    path = Path(model_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Nạp theo từng giờ luôn đọc được bản cũ hoặc bản mới hoàn chỉnh.
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.tmp', delete=False) as file:
        temporary = Path(file.name)
    try:
        joblib.dump(bundle, temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    path.with_suffix('.metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(f"Đã huấn luyện {len(X_train)} mẫu, kiểm thử {len(X_test)} mẫu.")
    print(f"MAE: {metrics['mae_vnd']:,.0f} VND; RMSE: {metrics['rmse_vnd']:,.0f} VND; R²: {metrics['r2']:.4f}")
    print(f'Đã lưu: {path.name}')
    return metrics


def execute_retrain(engine=None, model_path=MODEL_PATH):
    return train_model(load_data_from_db(engine), model_path)


def main():
    configure_console()
    try:
        execute_retrain()
    except (ValueError, OSError, SQLAlchemyError) as error:
        print(f'Không thể huấn luyện: {error}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
