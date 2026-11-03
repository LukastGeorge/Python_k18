"""Ràng buộc dữ liệu thống nhất cho nhập CSV, huấn luyện và dự đoán."""
import numpy as np
import pandas as pd
from config import FEATURES


def validate_features(frame):
    if not set(FEATURES).issubset(frame.columns):
        raise ValueError('Thiếu cột: ' + ', '.join(sorted(set(FEATURES) - set(frame.columns))))
    values = frame[FEATURES].apply(pd.to_numeric, errors='coerce')
    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError('Diện tích, số phòng và tọa độ phải là số hữu hạn, không để trống.')
    if not values.dien_tich.between(10, 1000).all():
        raise ValueError('Diện tích phải trong khoảng 10–1.000 m².')
    if not values.so_phong_ngu.between(0, 30).all() or values.so_phong_ngu.mod(1).ne(0).any():
        raise ValueError('Số phòng ngủ phải là số nguyên từ 0 đến 30.')
    if not values.latitude.between(-90, 90).all() or not values.longitude.between(-180, 180).all():
        raise ValueError('Tọa độ nằm ngoài phạm vi hợp lệ.')
    values['so_phong_ngu'] = values.so_phong_ngu.astype(int)
    return values
