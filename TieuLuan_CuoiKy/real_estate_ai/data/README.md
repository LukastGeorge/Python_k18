# Dữ liệu đầu vào

- `raw/kaggle_vietnam_2024/`: nguồn chính Kaggle Vietnam Housing Dataset 2024 phiên bản 8; CSV 30.229 dòng, 12 cột; Price theo tỷ VND. Manifest ghi schema và SHA256.
- `raw/kingcounty/`: nguồn King County tham khảo riêng. Dữ liệu TiniX tải trước được giữ trong `raw/vietnam/` và không dùng cho mô hình hiện hành.
- `input/`: mẫu CSV và các file nhập cho pipeline VND. Sao chép `input_template.csv` để tạo file dữ liệu riêng; không sửa trực tiếp dataset gốc.

Database ở `../storage/`; mô hình Việt Nam đang dùng nằm ở `../artifacts/vietnam/`. Nguồn Kaggle không có ngày đăng hoặc cột loại nhà. Các phần King County và pipeline cũ dùng mô hình riêng.
