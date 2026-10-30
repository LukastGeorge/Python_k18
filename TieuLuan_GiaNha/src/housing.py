"""Các bước tiền xử lý, huấn luyện và kiểm tra dữ liệu dùng chung với ứng dụng."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
TARGET = "SalePrice"
NUMERIC = ["Lot Area", "Gr Liv Area", "Overall Qual", "Overall Cond", "Year Built",
           "Year Remod/Add", "Bedroom AbvGr", "Full Bath", "Garage Cars", "Garage Area", "Total Bsmt SF"]
CATEGORICAL = ["Neighborhood", "Bldg Type", "House Style", "Central Air"]
FEATURES = NUMERIC + CATEGORICAL
LABELS = {"Lot Area": "Diện tích đất (ft²)", "Gr Liv Area": "Diện tích ở trên mặt đất (ft²)",
          "Overall Qual": "Chất lượng tổng thể (1–10)", "Overall Cond": "Tình trạng tổng thể (1–10)",
          "Year Built": "Năm xây dựng", "Year Remod/Add": "Năm cải tạo",
          "Bedroom AbvGr": "Số phòng ngủ trên mặt đất", "Full Bath": "Số phòng tắm đầy đủ trên mặt đất",
          "Garage Cars": "Sức chứa gara (ô tô)", "Garage Area": "Diện tích gara (ft²)",
          "Total Bsmt SF": "Diện tích tầng hầm (ft²)", "Neighborhood": "Khu vực tại Ames",
          "Bldg Type": "Loại nhà", "House Style": "Kiểu nhà", "Central Air": "Điều hòa trung tâm"}
INTEGER_FIELDS = ["Overall Qual", "Overall Cond", "Year Built", "Year Remod/Add",
                  "Bedroom AbvGr", "Full Bath", "Garage Cars"]


class QuantileClipper(TransformerMixin, BaseEstimator):
    """Giới hạn các giá trị cực đoan theo phân vị học trên train của mỗi fold."""
    def __init__(self, lower=0.01, upper=0.99):
        self.lower = lower
        self.upper = upper

    def fit(self, X, y=None):
        values = np.asarray(X, dtype=float)
        self.low_ = np.nanquantile(values, self.lower, axis=0)
        self.high_ = np.nanquantile(values, self.upper, axis=0)
        self.n_features_in_ = values.shape[1]
        return self

    def transform(self, X):
        return np.clip(np.asarray(X, dtype=float), self.low_, self.high_)


def make_pipeline(estimator):
    number_steps = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("clip", QuantileClipper()),
        ("scale", StandardScaler()),
    ])
    category_steps = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    prepare = ColumnTransformer([
        ("number", number_steps, NUMERIC),
        ("category", category_steps, CATEGORICAL),
    ])
    return Pipeline([("prepare", prepare), ("regressor", estimator)])


def load_and_clean(path=None):
    path = Path(path) if path else ROOT / "data/raw/AmesHousing.tsv"
    raw = pd.read_csv(path, sep="\t")
    required = ["PID", TARGET] + FEATURES
    missing = set(required) - set(raw.columns)
    if missing:
        raise ValueError(f"Dataset thiếu cột: {sorted(missing)}")
    data = raw[required].copy()
    for col in NUMERIC + [TARGET]:
        data[col] = pd.to_numeric(data[col], errors="coerce")
        data.loc[~np.isfinite(data[col]), col] = np.nan
    for col in CATEGORICAL:
        data[col] = data[col].map(lambda x: x.strip() if isinstance(x, str) else x)
        data[col] = data[col].replace("", np.nan)
    before = len(data)
    data = data.drop_duplicates(subset="PID", keep="last")
    duplicate_count = before - len(data)
    invalid = data[TARGET].isna() | (data[TARGET] <= 0)
    for col in ["Lot Area", "Gr Liv Area"]:
        invalid |= data[col].notna() & (data[col] <= 0)
    cleaned = data.loc[~invalid].reset_index(drop=True)
    audit = {"raw_rows": len(raw), "raw_columns": len(raw.columns), "clean_rows": len(cleaned),
             "duplicate_ids_removed": duplicate_count, "invalid_rows_removed": int(invalid.sum()),
             "raw_missing_cells": int(raw.isna().sum().sum()),
             "selected_missing_cells": int(cleaned[FEATURES].isna().sum().sum()),
             "missing_by_column": raw.isna().sum().sort_values(ascending=False).head(12).to_dict()}
    return raw, cleaned, audit


def load_metadata():
    return json.loads((ROOT / "artifacts/metadata.json").read_text(encoding="utf-8"))


def validate_inputs(frame, metadata):
    """Kiểm tra schema và miền dữ liệu; giữ NaN số để pipeline điền từ train."""
    if frame.empty:
        raise ValueError("Chưa có căn nhà nào để dự đoán.")
    if len(frame) > 2000:
        raise ValueError("Mỗi lần chỉ xử lý tối đa 2.000 căn nhà.")
    if frame.columns.duplicated().any():
        raise ValueError("Tên cột không được trùng nhau.")
    missing = set(FEATURES) - set(frame.columns)
    if missing:
        raise ValueError("Thiếu cột: " + ", ".join(sorted(missing)))
    data = frame[FEATURES].copy()
    for col in NUMERIC:
        values = pd.to_numeric(data[col], errors="coerce")
        if (data[col].notna() & values.isna()).any() or np.isinf(values.to_numpy(dtype=float)).any():
            raise ValueError(f"{LABELS[col]} phải là số hữu hạn hoặc để trống.")
        lower, upper = metadata["input_bounds"][col]
        if ((values < lower) | (values > upper)).any():
            raise ValueError(f"{LABELS[col]} phải trong khoảng {lower:g}–{upper:g} của tập huấn luyện.")
        if col in INTEGER_FIELDS and ((values.dropna() % 1) != 0).any():
            raise ValueError(f"{LABELS[col]} phải là số nguyên.")
        data[col] = values.astype(float)
    for col in CATEGORICAL:
        data[col] = data[col].map(lambda v: v.strip() if isinstance(v, str) else v)
        if not data[col].isin(metadata["categories"][col]).all():
            raise ValueError(f"{LABELS[col]} có giá trị trống hoặc chưa được hỗ trợ.")
    if (data["Year Remod/Add"] < data["Year Built"]).any():
        raise ValueError("Năm cải tạo không thể trước năm xây dựng.")
    return data


def predict_prices(model, frame, metadata):
    clean = validate_inputs(frame, metadata)
    predicted = np.asarray(model.predict(clean), dtype=float)
    if not np.isfinite(predicted).all() or (predicted <= 0).any():
        raise ValueError("Mô hình không cho kết quả hợp lệ với tổ hợp thông số này.")
    output = clean.copy()
    output["PredictedPrice_USD"] = np.round(predicted, 2)
    return output
