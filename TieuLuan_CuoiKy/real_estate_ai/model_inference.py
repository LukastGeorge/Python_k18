"""Nạp mô hình thật hoặc công thức minh họa được gắn nhãn rõ ràng."""
import numpy as np
import joblib
from config import FEATURES, MODEL_PATH
from validation import validate_features


class RealEstateAI:
    def __init__(self, model_path=MODEL_PATH, allow_demo=False):
        self.model = None
        self.method = 'unavailable'
        try:
            bundle = joblib.load(model_path)
        except FileNotFoundError:
            if allow_demo:
                self.method = 'demo_formula'
            return
        except Exception as error:
            raise ValueError('Không đọc được mô hình. Kiểm tra file hoặc huấn luyện lại; không tự thay bằng mô hình giả.') from error
        if (not isinstance(bundle, dict) or bundle.get('features') != FEATURES
                or bundle.get('target') != 'actual_price' or bundle.get('currency') != 'VND'
                or not hasattr(bundle.get('model'), 'predict')):
            raise ValueError('File mô hình không đúng định dạng của dự án. Cần huấn luyện lại.')
        self.model = bundle['model']
        self.method = 'trained_model'

    def predict_price(self, clean_data):
        features = validate_features(clean_data)
        if features.empty:
            return np.array([], dtype=float)
        if self.model is not None:
            predictions = np.asarray(self.model.predict(features), dtype=float)
        elif self.method == 'demo_formula':
            predictions = (features.dien_tich * 40_000_000 + features.so_phong_ngu * 50_000_000).to_numpy()
        else:
            return np.full(len(features), np.nan)
        if not np.isfinite(predictions).all() or (predictions <= 0).any():
            raise ValueError('Mô hình tạo giá không hợp lệ với dữ liệu đầu vào này.')
        return predictions
