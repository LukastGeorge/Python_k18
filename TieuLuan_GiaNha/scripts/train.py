"""Chạy từ thư mục dự án: python -m scripts.train."""
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from src.housing import ROOT, FEATURES, NUMERIC, CATEGORICAL, TARGET, make_pipeline, load_and_clean


def main():
    artifacts = ROOT / "artifacts"
    artifacts.mkdir(exist_ok=True)
    (ROOT / "data/processed").mkdir(exist_ok=True)
    raw, data, audit = load_and_clean()
    raw.to_csv(ROOT / "data/raw/ames_housing.csv", index=False)
    data.to_csv(ROOT / "data/processed/housing.csv", index=False)
    X_train, X_test, y_train, y_test = train_test_split(
        data[FEATURES], data[TARGET], test_size=0.2, random_state=42)
    folds = KFold(n_splits=5, shuffle=True, random_state=42)
    models = {
        "Median baseline": DummyRegressor(strategy="median"),
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=250, max_depth=2, learning_rate=0.05,
                                                       loss="huber", random_state=42),
    }
    fitted, rows = {}, []
    for name, regressor in models.items():
        model = make_pipeline(regressor)
        cv = -cross_val_score(model, X_train, y_train, cv=folds,
                             scoring="neg_root_mean_squared_error", n_jobs=1)
        model.fit(X_train, y_train)
        pred = model.predict(X_test)
        rows.append({"model": name, "cv_rmse_mean": cv.mean(), "cv_rmse_std": cv.std(),
                     "test_mae": mean_absolute_error(y_test, pred),
                     "test_rmse": root_mean_squared_error(y_test, pred), "test_r2": r2_score(y_test, pred)})
        fitted[name] = model
        print(name, rows[-1], flush=True)
    metrics = pd.DataFrame(rows).sort_values("cv_rmse_mean").reset_index(drop=True)
    best_name = metrics.iloc[0]["model"]
    best = fitted[best_name]
    metrics.to_csv(artifacts / "metrics.csv", index=False)
    joblib.dump(best, artifacts / "model.joblib", compress=3)
    # Test chỉ được dùng để đánh giá cuối cùng, không chọn mô hình/siêu tham số.
    predictions = pd.DataFrame({"PID": data.loc[X_test.index, "PID"], "actual_usd": y_test,
                                "predicted_usd": best.predict(X_test)})
    predictions["residual_usd"] = predictions.actual_usd - predictions.predicted_usd
    predictions.to_csv(artifacts / "test_predictions.csv", index=False)
    importance = permutation_importance(best, X_test, y_test, n_repeats=5, random_state=42,
                                         scoring="neg_root_mean_squared_error", n_jobs=1)
    pd.DataFrame({"feature": FEATURES, "increase_rmse": importance.importances_mean,
                  "std": importance.importances_std}).sort_values("increase_rmse", ascending=False).to_csv(
                      artifacts / "feature_importance.csv", index=False)
    split = {"train_pid": data.loc[X_train.index, "PID"].astype(int).tolist(),
             "test_pid": data.loc[X_test.index, "PID"].astype(int).tolist()}
    (artifacts / "split.json").write_text(json.dumps(split, indent=2), encoding="utf-8")
    metadata = {"dataset": "Ames Housing", "source": "https://jse.amstat.org/v19n3/decock/AmesHousing.txt",
                "dataset_sha256": hashlib.sha256((ROOT / "data/raw/AmesHousing.tsv").read_bytes()).hexdigest(),
                "created_utc": datetime.now(timezone.utc).isoformat(), "market": "Ames, Iowa, USA (2006–2010)",
                "currency": "USD", "features": FEATURES, "target": TARGET, "seed": 42,
                "train_rows": len(X_train), "test_rows": len(X_test), "cv_folds": 5,
                "selected_model": best_name, "selection_rule": "Lowest 5-fold CV RMSE on training data",
                "defaults": {c: float(X_train[c].median()) for c in NUMERIC},
                "categories": {c: sorted(X_train[c].dropna().unique().tolist()) for c in CATEGORICAL},
                "input_bounds": {c: [float(X_train[c].min()), float(X_train[c].max())] for c in NUMERIC},
                "versions": {name: importlib.metadata.version(name) for name in
                             ["numpy", "pandas", "scikit-learn", "joblib", "matplotlib", "seaborn", "streamlit"]},
                "audit": audit}
    for c in CATEGORICAL:
        metadata["defaults"][c] = X_train[c].mode().iloc[0]
    (artifacts / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    X_train.head(10).to_csv(ROOT / "data/sample_input.csv", index=False)
    print("Selected:", best_name, flush=True)


if __name__ == "__main__":
    main()
