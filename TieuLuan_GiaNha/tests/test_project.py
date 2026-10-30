import json
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
from src.housing import ROOT, FEATURES, QuantileClipper, load_metadata, load_and_clean, predict_prices, validate_inputs


@pytest.fixture(scope="module")
def bundle():
    return joblib.load(ROOT / "artifacts/model.joblib"), load_metadata()


@pytest.fixture
def sample(bundle):
    return pd.DataFrame([bundle[1]["defaults"]])


def test_train_test_disjoint_and_complete():
    split = json.loads((ROOT / "artifacts/split.json").read_text())
    _, data, _ = load_and_clean()
    assert not set(split["train_pid"]) & set(split["test_pid"])
    assert set(split["train_pid"]) | set(split["test_pid"]) == set(data.PID)


def test_clipper_does_not_learn_from_test():
    clip = QuantileClipper(lower=0, upper=1).fit([[1, 10], [2, 20]])
    assert np.array_equal(clip.transform([[1000, -10]]), [[2, 10]])
    assert np.array_equal(clip.high_, [2, 20])


def test_persisted_model_matches_report(bundle):
    model, meta = bundle
    data = pd.read_csv(ROOT / "data/processed/housing.csv").set_index("PID")
    predictions = pd.read_csv(ROOT / "artifacts/test_predictions.csv")
    actual_predictions = model.predict(data.loc[predictions.PID, FEATURES])
    assert np.allclose(actual_predictions, predictions.predicted_usd)
    scores = pd.read_csv(ROOT / "artifacts/metrics.csv").set_index("model")
    row = scores.loc[meta["selected_model"]]
    assert row.test_mae == pytest.approx(mean_absolute_error(predictions.actual_usd, actual_predictions))
    assert row.test_rmse == pytest.approx(root_mean_squared_error(predictions.actual_usd, actual_predictions))
    assert row.test_r2 == pytest.approx(r2_score(predictions.actual_usd, actual_predictions))
    assert meta["selected_model"] == scores.cv_rmse_mean.idxmin()


def test_single_and_batch_agree(bundle, sample):
    model, meta = bundle
    single = predict_prices(model, sample, meta).PredictedPrice_USD.iloc[0]
    batch = predict_prices(model, pd.concat([sample, sample], ignore_index=True), meta)
    assert list(batch.PredictedPrice_USD) == [single, single]
    assert single > 0


@pytest.mark.parametrize("value", ["not a number", np.inf, -np.inf, -10, 10**9])
def test_bad_area_rejected(bundle, sample, value):
    sample["Gr Liv Area"] = value
    with pytest.raises(ValueError):
        validate_inputs(sample, bundle[1])


def test_numeric_missing_imputed(bundle, sample):
    sample["Garage Area"] = np.nan
    assert predict_prices(bundle[0], sample, bundle[1]).PredictedPrice_USD.iloc[0] > 0


def test_fractional_count_rejected(bundle, sample):
    sample["Bedroom AbvGr"] = 2.5
    with pytest.raises(ValueError, match="số nguyên"):
        validate_inputs(sample, bundle[1])


def test_unknown_neighborhood_rejected(bundle, sample):
    sample["Neighborhood"] = "Ho Chi Minh City"
    with pytest.raises(ValueError, match="chưa được hỗ trợ"):
        validate_inputs(sample, bundle[1])


def test_year_order_rejected(bundle, sample):
    sample["Year Built"], sample["Year Remod/Add"] = 2000, 1960
    with pytest.raises(ValueError, match="Năm cải tạo"):
        validate_inputs(sample, bundle[1])


def test_missing_column_rejected(bundle, sample):
    with pytest.raises(ValueError, match="Thiếu cột"):
        validate_inputs(sample.drop(columns="Lot Area"), bundle[1])


def test_empty_and_oversized_rejected(bundle, sample):
    for frame in [sample.iloc[:0], pd.concat([sample] * 2001)]:
        with pytest.raises(ValueError):
            validate_inputs(frame, bundle[1])


def test_csv_sample_runs(bundle):
    frame = pd.read_csv(ROOT / "data/sample_input.csv")
    assert len(predict_prices(bundle[0], frame, bundle[1])) == 10


def test_app_pages_and_prediction():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / "app_ames.py"), default_timeout=45).run()
    assert not app.exception
    for page in ["Khám phá dữ liệu", "Đánh giá mô hình", "Dự đoán giá nhà"]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert "Giá dự đoán:" in app.success[0].value
    app.number_input(key="Year Built").set_value(2000)
    app.number_input(key="Year Remod/Add").set_value(1960)
    app.button[0].click().run()
    assert not app.exception
    assert "Năm cải tạo" in app.error[0].value
