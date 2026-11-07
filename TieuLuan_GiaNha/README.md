<<<<<<< HEAD
# Python_k18
=======
# Dự đoán giá từng căn nhà ở Mỹ · Nhóm 8

Nguyễn Duy Trường — MSSV 24150180 — STT 6. Cá nhân, nhóm 8; ngành Công nghệ thông tin, chuyên ngành Kỹ thuật phần mềm.

## Chạy ngay trên máy này

Mở PowerShell và chạy:

```powershell
cd E:\Workspace\Python_k18\TieuLuan_GiaNha
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Hoặc nhấp đúp `chay_demo.cmd`. Mở http://localhost:8501 theo địa chỉ terminal; Ctrl+C để dừng. Không cần Activate.ps1. Database và mô hình đã có sẵn, chạy demo ngoại tuyến được.

Nếu cài trên máy mới (Python 3.12):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Phạm vi thực tế — bản ngày 26/10/2026

Mục tiêu database là **50 bang + Washington, D.C.**, giai đoạn **2016–2026**. Theo lựa chọn chỉ dùng nguồn miễn phí, bản hiện tại có **48.584 giao dịch** ở **2/51 khu vực**:

| Khu vực có dữ liệu | Số giao dịch sau lọc | Ngày bán từ–đến | Phạm vi |
|---|---:|---|---|
| Colorado (CO) | 23.449 | 04/01/2016–09/09/2026 | Chỉ Boulder County; không phủ toàn bang |
| Washington, D.C. (DC) | 25.135 | 04/01/2016–15/10/2026 | Các nhà một đơn vị đủ điều kiện trong CAMA |

**49 bang còn lại chưa có dữ liệu trong bản này.** Có bản ghi ở một năm không có nghĩa đã lấy đủ giao dịch của năm. Năm 2026 chưa kết thúc. Trang **Độ phủ 51 khu vực** và `artifacts/us/coverage_by_state_year.csv` ghi số mẫu cho đủ 561 tổ hợp khu vực–năm, kể cả số 0.

Giá là giá bán từng căn gắn với ngày bán, không dùng ZHVI trung bình bang, không ghép giá niêm yết hiện tại với `prev_sold_date`. Đặc điểm nhà lấy từ bản ghi hiện tại của cơ quan thuế; chưa có phiên bản đặc điểm đúng tại từng ngày giao dịch. Vì vậy điểm kiểm thử không chứng minh khả năng dự báo lịch sử thực tế. Nguồn hiện tại cũng bỏ sót các tài sản không còn trong hồ sơ hiện hành.

## Chức năng

- Tổng quan nguồn, số mẫu, thời gian và phần thiếu.
- Khám phá biểu đồ chồng giá trung vị hai khu vực theo tháng, phân phối và diện tích/giá; lọc, xuất CSV.
- Dự đoán một căn theo bang, quận/thành phố, diện tích, phòng ngủ, phòng tắm, năm xây, tháng/năm định giá. Nhập m² hoặc ft².
- Dự đoán CSV: dùng `data/us_sample_input.csv`, tối đa 2.000 dòng/4 MB.
- Chọn một bang chưa có dữ liệu sẽ hiện thông báo và không đưa giá dự đoán.
- Xem đánh giá mô hình và bảng độ phủ toàn bộ 51 khu vực.

Diện tích Boulder là **TotalFinishedSF** (tổng diện tích hoàn thiện); D.C. là **GBA** (diện tích xây dựng). Trường `area_kind` lưu khác biệt này, không đổi tên cả hai thành diện tích ở. Phòng tắm quy đổi: đầy đủ = 1, ba phần tư = 0,75, một nửa = 0,5. 1 ft² = 0,09290304 m².

## Database và mã nguồn

```text
app.py                         Điểm chạy giao diện mới
src/us_app.py                  Các trang Streamlit
src/us_housing.py              Kiểm tra dữ liệu, độ phủ, dự đoán
scripts/fetch_us_data.py        Tải nguồn công khai, lưu SHA-256
scripts/build_us_database.py    Làm sạch, chuẩn hóa, tạo SQLite
scripts/train_us.py             Chọn mô hình theo thời gian, đánh giá, lưu
 data/us_housing.sqlite3        Database chính (~14 MB)
 data/raw/us/                   Snapshot gốc và manifest nguồn
 data/us_sample_input.csv       Mẫu nhập dự đoán mới
artifacts/us/                   Mô hình, điểm số, test, độ phủ, audit
app_ames.py                     Demo Ames cũ, giữ để tham khảo
```

SQLite có bảng `states`, `sources`, `sales`, `coverage`; không cần MySQL/PostgreSQL. `sales` lưu mã giao dịch/căn nhà, bang, locality, giá USD, ngày bán, diện tích/loại diện tích, số phòng, năm xây, nguồn và thời điểm snapshot đặc điểm. Không lưu tên chủ sở hữu.

## Cập nhật dữ liệu và huấn luyện lại

Các lệnh sau chạy trong thư mục dự án; bước tải cần Internet, các bước còn lại chạy ngoại tuyến:

```powershell
.\.venv\Scripts\python.exe -m scripts.fetch_us_data --refresh
.\.venv\Scripts\python.exe -m scripts.build_us_database
.\.venv\Scripts\python.exe -m scripts.train_us
.\.venv\Scripts\python.exe -m pytest -q
```

`--source dc` hoặc `--source boulder` chỉ tải một nguồn. Không có `--refresh` thì tái sử dụng hai CSV Boulder đã có. Database được dựng ra tệp tạm rồi thay thế sau kiểm tra; ứng dụng từ chối mô hình nếu mã SHA-256 database không khớp. Khởi động lại Streamlit sau khi cập nhật.

Hiện chỉ có hai bộ chuyển đổi nguồn đã xác minh. Thêm bang cần nguồn giao dịch hợp lệ và adapter ánh xạ đúng giá–ngày, diện tích, số phòng, quận/thành phố, mã căn nhà; không chỉ thêm tên bang vào form. Xem `docs/DU_LIEU_MY_2016_2026.md`.

## Mô hình và kiểm thử

Train 2016–2023: 34.706 dòng. Validation 2024: 4.214 dòng. Test 2025–2026: 7.804 dòng. Loại 1.860 giao dịch cũ của căn nhà thuộc tập giữ lại để tránh cùng căn xuất hiện ở hai tập.

So sánh median baseline, Ridge, Random Forest, Histogram Gradient Boosting; chọn bằng RMSE validation. Biến đổi log1p của giá và StandardScaler/OneHotEncoder nằm trong pipeline, chỉ fit trên tập huấn luyện tương ứng.

**Histogram Gradient Boosting** được chọn. Mô hình đánh giá fit train + validation, test riêng đạt:

- MAE: **265.745,75 USD**.
- RMSE: **520.761,74 USD**.
- R²: **0,6862**.

Sai số còn lớn, thiếu vị trí chi tiết/chất lượng nhà và vintage đặc điểm. Đây là demo học máy, chưa phải công cụ định giá đủ tin cậy để sử dụng thực tế. R² không phải phần trăm đoán đúng.

`evaluation_model.joblib` tái lập điểm trên; `model.joblib` dùng trên giao diện là bản fit lại trên toàn bộ 48.584 dòng, bao gồm dữ liệu mới. Không công bố điểm test của bản fit toàn bộ như điểm độc lập. Chỉ nạp joblib do dự án tạo hoặc từ nguồn tin cậy.

Kiểm thử hiện tại: **36 test đạt**, gồm bản mới và kiểm tra hồi quy Ames cũ. Có kiểm tra khóa ngoại/toàn vẹn SQLite, đủ 51×11 ô độ phủ, ngày tương lai, đầu vào xấu, chống trùng căn giữa các tập, tái lập điểm số và các trang giao diện.

## Nguồn miễn phí

- [Boulder County Assessor — Data Download](https://bouldercounty.gov/property-and-land/assessor/data-download/): Buildings.csv, Sales.csv.
- [DC GIS — Residential CAMA](https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Property_and_Land_WebMercator/FeatureServer/25).
- [DC GIS — mô tả trường dữ liệu](https://dcatlas.dcgis.dc.gov/metadata/CamaResPt.html).

Nguồn là dữ liệu mở của cơ quan địa phương, không bảo đảm bao phủ toàn quốc. Giữ liên kết nguồn, manifest và các giới hạn khi chia sẻ. Chưa đăng dự án lên GitHub.

## Bản cũ

Ames 2006–2010, mô hình cũ và script `scripts/train.py` vẫn được giữ nguyên. Chạy `python -m streamlit run app_ames.py`; hướng dẫn cũ ở `docs/README_AMES_LEGACY.md`. Không trộn số liệu đánh giá Ames với bộ dữ liệu mới.
>>>>>>> 2593673 (TieuLuan)
