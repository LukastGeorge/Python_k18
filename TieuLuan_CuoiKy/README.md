# Dự đoán giá nhà tại TP.HCM và Hà Nội từ Kaggle 2024

Nguồn chính: [House Price Prediction Dataset Vietnam 2024](https://www.kaggle.com/datasets/nguyentiennhan/vietnam-housing-dataset-2024) của Nguyen Tien Nhan, **phiên bản 8**, CC0 Public Domain. CSV có **30.229 dòng và 12 cột**; giữ **22.183 tin** ở hai thành phố sau lọc. Price theo **tỷ VND**, được nhân 1e9 để huấn luyện và phục vụ bằng VND. Nguồn không có ngày đăng từng tin hoặc cột loại nhà.

## Chạy chương trình

Máy hiện tại đã có môi trường và model. Từ thư mục Python_k18:

```powershell
.\TieuLuan_CuoiKy\chay_ui.cmd
```

Mở **http://127.0.0.1:8000**, chọn tin mẫu hoặc nhập thông tin rồi dự đoán. Giữ terminal mở; Ctrl+C để dừng. Dùng SQLite, không cần bật PostgreSQL. Cài mới bằng `TieuLuan_CuoiKy/scripts/cai_dat.cmd` với Python 3.12.

## Báo cáo và notebook đang dùng

- **Word mới theo yêu cầu**: [44_NguyenDuyTruong_24150180.docx](docs/44_NguyenDuyTruong_24150180.docx), nguồn Kaggle 2024.
- [Notebook Việt Nam đã chạy](notebooks/PhanTich_GiaNha_VietNam.ipynb).
- [Notebook nhóm](notebooks/TeamWork_PP_Nhom8.ipynb): phần Việt Nam ở mục 6, các mục King County trước đó là tham khảo.
- [Nguồn và tái lập](docs/VIET_NAM.md).
- [PowerPoint 24 slide](docs/Thuyet_trinh_TieuLuan_CuoiKy.pptx): cùng dataset, số liệu, sáu feature OLS và ví dụ dự đoán với Word.
- Word giữ mẫu gốc Đại học Gia Định: bìa, phiếu chấm, mục lục, danh mục hình/bảng và bố cục sáu chương. Mẫu nguồn được giữ riêng trong docs/templates.

## Phương pháp và kết quả

12 cột gốc gồm Price và 11 cột dự báo ban đầu. Loại hướng ban công vì thiếu 87.2% trên train; tách Address thành 3 nhóm địa bàn. Kết quả có **12 nhóm đầu vào** gồm 6 biến số và 6 nhóm danh mục, mã hóa thành **166 cột OLS**.

OLS chọn **6 nhóm**: diện tích, quận/huyện, số tầng, phường/xã, pháp lý và đường trước nhà. Độ quan trọng đo bằng mức tăng RMSE log validation khi bỏ một nhóm rồi fit lại. Diện tích đứng đầu. Bộ gọn nhất nằm trong 1% sai số tốt nhất được chọn; đây là thí nghiệm tuyến tính riêng.

Ứng dụng dùng **XGBoost với 12 đầu vào**. Test **3.318 tin**: R² **0,644**, MAE **0,923 tỷ**, RMSE **1,225 tỷ**, MdAPE **12,1%**; **72,9%** tin trong sai lệch ±20%. Khoảng 90% danh nghĩa có độ phủ thực **89,6%**. Chưa so XGBoost sáu biến với XGBoost 12 biến.

Chia theo nhóm địa chỉ chuẩn hóa + diện tích làm tròn 0,1 m²: train 13.398, validation 3.271, calibration 2.196, test 3.318. Các tập không chung nhóm. Đây không phải kiểm thử theo thời gian. Giá dữ liệu giữ lại chỉ từ 1 đến 11,5 tỷ VND; không suy rộng chất lượng sang phân khúc cao hơn hoặc giá hiện tại.

## Huấn luyện và kiểm tra

Trong real_estate_ai:

```powershell
.\.venv\Scripts\python.exe -m backend.train_vietnam --clean artifacts/vietnam/listings_clean.csv.gz --import-db
.\.venv\Scripts\python.exe -m pytest -q
```

`scripts/huan_luyen.cmd` chạy huấn luyện từ CSV sạch có checksum. Chạy tiếp `scripts/analyze_vietnam_linear.py` và `scripts/build_vietnam_evidence.py` bằng Python trong .venv nếu cần tạo lại phân tích. Catalog Kaggle lưu trong `vietnam_2024_listings`; dữ liệu nhập trước đây và lịch sử người dùng được giữ. `vietnam_predictions` lưu dự đoán kèm phiên bản; API lịch sử chỉ trả model hiện hành. Không dùng dự đoán làm nhãn.

Kiểm thử bản Kaggle: **100 bài đạt, 1 bài PostgreSQL bỏ qua**. Kiểm tra đơn vị giá, schema, chuẩn hóa địa chỉ, nhóm không trùng, loại holdout khỏi fit, TreeSHAP, metric, API, nhập catalog và launcher khi cổng bận hoặc có phiên mã nguồn cũ.

Launcher dùng lại phiên đang chạy khi khớp mã nguồn và model. Nếu cổng 8000 có phiên khác, tự chọn cổng trống và in URL. Khi cần kiểm tra khởi động mà không mở trình duyệt: `chay_ui.cmd --no-browser --check-only`.

## Docker

Model/artifact mới nằm trong nguồn Docker hiện tại; chưa build hoặc phát hành image mới. Image GHCR đã xuất bản trước đây chưa được cập nhật bằng thao tác này. King County vẫn có tại `/kingcounty`, công cụ cũ tại `/legacy`.
