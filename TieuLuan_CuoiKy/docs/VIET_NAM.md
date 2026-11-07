# Nguồn Kaggle Vietnam Housing 2024 và cách tái lập

[Dataset](https://www.kaggle.com/datasets/nguyentiennhan/vietnam-housing-dataset-2024) · Nguyen Tien Nhan · phiên bản 8 · cập nhật 22/09/2024 · CC0 Public Domain theo Kaggle metadata. Theo tác giả, thu thập từ batdongsan.vn. CSV `vietnam_housing_dataset.csv`, 30.229 dòng, 12 cột. SHA256: `7ee188d69aca06349a81bac0c2d2d1503058d5aec7124edfd075154fa87d97c8`.

Price theo tỷ VND, nhân 1e9; Area m², Frontage/Access Road m. Không có ngày đăng, loại nhà hoặc ID thật. Chỉ lấy TP.HCM/Hà Nội; sửa Unicode, dấu chấm cuối và các alias thành phố. Giữ giá 0,5–200 tỷ, diện tích 15–1.000m², đơn giá 5–800 triệu/m². Thực tế còn 22.183 tin, giá 1–11,5 tỷ. Có 17.035 nhóm địa chỉ–diện tích; không coi mọi dòng cùng nhóm là căn trùng đã xác minh.

Nhóm theo địa chỉ chuẩn hóa và diện tích làm tròn 0,1 m², không dùng Price. GroupShuffleSplit tạo train/validation/calibration/test với xấp xỉ 60/15/10/15% nhóm, seeds 42/43/44. Nghiêm cấm gọi đây là split theo thời gian. Thống kê điền thiếu, chuẩn hóa và one-hot chỉ fit trên train. Sau chọn XGBoost, fit train+validation; calibration chỉ hiệu chỉnh khoảng; test giữ riêng.

12 cột nguồn gồm Price và 11 ứng viên; bỏ Balcony direction vì >80% thiếu ở train; Address thành ba nhóm địa bàn. 12 nhóm model (6 số + 6 danh mục). OLS log(VND), log(area), StandardScaler; drop-column refit trên validation, chọn prefix nhỏ nhất trong 1% sai số tốt nhất. Bộ chọn 6 biến: area, district_name, floor_count, ward_name, legal_status, road_width. OLS gọn là phân tích riêng; app dùng XGBoost 12 nhóm.

Trong `real_estate_ai`, `.venv/Scripts/python.exe -m backend.train_vietnam` huấn luyện từ raw CSV được xác minh. Có thể dùng `--clean artifacts/vietnam/listings_clean.csv.gz --import-db` với manifest sạch kèm SHA256. Sau đó chạy lần lượt `../scripts/analyze_vietnam_linear.py`, `../scripts/build_vietnam_evidence.py`, `../scripts/extend_vietnam_notebook.py` bằng Python trong .venv. Builder Word là `scripts/build_vietnam_report.py`, dùng runtime Documents của Codex.

Catalog mới dùng bảng vietnam_2024_listings, giữ nguyên dữ liệu cũ. Không dùng giá do app dự đoán làm nhãn. Model_version hiện tại: `vn2024-8ea036e9d9fe`. Bản báo cáo được cập nhật là `44_NguyenDuyTruong_24150180.docx`; PPT 24 slide cùng dùng nguồn Kaggle và artifact này. Word được dựng từ docs/templates/mau_bao_cao_goc.docx, giữ cấu trúc sáu chương; không dùng lại bộ định dạng báo cáo chung.
