# Ứng dụng Kaggle Vietnam Housing 2024

Backend Flask, frontend HTML/JS, mô hình XGBoost và SQLite. Hướng dẫn chạy, số liệu và file Word mới ở [README dự án](../README.md).

| Vị trí | Nội dung |
|---|---|
| backend/kaggle_vietnam.py | Xác minh nguồn, parse địa chỉ và chia nhóm |
| backend/vietnam.py | Pipeline, kiểm tra đầu vào, dự đoán và TreeSHAP |
| backend/train_vietnam.py | Huấn luyện, calibration và test |
| backend/vietnam_api.py | API info, predict, history và biểu đồ |
| backend/import_vietnam_data.py | Nhập catalog vào vietnam_2024_listings |
| frontend/templates/vietnam.html | Giao diện chính |
| artifacts/vietnam | Model, CSV sạch, split, metric, biểu đồ và ví dụ |
| data/raw/kaggle_vietnam_2024 | CSV gốc, metadata, manifest và SHA256 |

12 nhóm đầu vào: area, bedroom_count, bathroom_count, floor_count, frontage_width, road_width, province_name, district_name, ward_name, house_direction, legal_status, furniture_state. Không nhận Price hoặc giá/m² làm đầu vào. Hướng ban công được loại; nguồn không có loại nhà hoặc ngày đăng.

`GET /api/vietnam/info` trả nguồn và ví dụ. `POST /api/vietnam/predict` nhận JSON thông tin căn nhà, trả VND, khoảng 90%, giải thích và tin đối chiếu. `GET /api/vietnam/history` trả mười dự đoán của model hiện hành. Lịch sử cũ vẫn còn trong database theo model_version. Biểu đồ mô tả chỉ dùng train, biểu đồ TreeSHAP toàn cục dùng 600 tin calibration chưa fit.
