# Bản tích hợp King County ngày 07 tháng 11 năm 2026

Giao diện chính dùng cùng dataset với `notebooks/TeamWork_PP_Nhom8.ipynb`. Nhà thuộc King County, Washington, Mỹ, giao dịch năm 2014–2015. Mô hình học giá USD và hiển thị VND quy đổi theo snapshot Vietcombank **25.780 VND/USD**. Đây không phải mô hình định giá nhà Việt Nam hoặc giá thị trường hiện tại.

## Khởi động

Từ thư mục gốc repository:

```powershell
.\TieuLuan_CuoiKy\chay_ui.cmd
```

Mở http://127.0.0.1:8000. Chọn một căn nhà trong tập test để đối chiếu giá thật, giá dự đoán, VND/m², khoảng dự đoán, TreeSHAP và những giao dịch đã bán trước ngày định giá. Công cụ nhập dữ liệu cũ được giữ tại `/legacy`.

Nếu chưa có môi trường, chạy `scripts/cai_dat.cmd`. Các artifact mô hình và biểu đồ đã có trong `real_estate_ai/artifacts/kingcounty/`. Khi cần dựng lại:

```powershell
cd .\TieuLuan_CuoiKy\real_estate_ai
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='2'
$env:DB_BACKEND='sqlite'
.\.venv\Scripts\python.exe -m backend.train_kingcounty --import-db
.\.venv\Scripts\python.exe ..\scripts\build_kingcounty_evidence.py
.\.venv\Scripts\python.exe -m pytest -q
```

Bước tạo hình cần thư viện trong `requirements/notebook.txt`. Nút chạy huấn luyện `scripts/huan_luyen.cmd` chọn SQLite và không xóa dữ liệu cũ.

## Kết quả có thể tái lập

- Gốc: 21.613 giao dịch, 21 thuộc tính. Giữ 21.584 giao dịch sau kiểm tra quy tắc; danh sách 29 mã bị loại nằm trong metadata.
- Train 05–10/2014: 11.596 dòng. Validation 11–12/2014: 2.853 dòng. Calibration 01–02/2015: 2.218 dòng. Test 03–05/2015: 4.750 dòng.
- Loại 167 giao dịch trước đó của mã nhà thuộc tập phía sau. Các tập không chung mã căn nhà.
- Chọn **XGBoost nhà và vị trí** bằng RMSE validation. Mô hình phục vụ fit train + validation, không fit calibration hoặc test.
- Test: MAE **76.538,44 USD**, RMSE **131.886,28 USD**, R² **0,8734**. Tỷ lệ sai lệch không quá ±20%: **79,5%**.
- Khoảng dự đoán 90% danh nghĩa có độ phủ test **90,8%**. Bề rộng khoảng trung vị **6,82 tỷ VND** quy đổi; không bảo đảm độ phủ ở thị trường thay đổi.
- 73 kiểm thử cục bộ đạt; kiểm thử PostgreSQL chưa chạy. Notebook chạy 20 code cell và có 15 đầu ra hình, không lỗi.

Không so trực tiếp R² này với thí nghiệm bốn biến cũ dùng phép chia nhóm ngẫu nhiên. So sánh đặc trưng phải dựa trên cùng validation.

## Đầu vào và giải thích

Nhập riêng diện tích ở và diện tích đất (m²), phòng ngủ, phòng tắm quy đổi, số tầng, grade, vị trí, mã bưu chính, năm xây/cải tạo, tình trạng, cảnh quan, ven nước và ngày định giá lịch sử. API chặn tọa độ ngoài miền King County và ngày ngoài 02/05/2014–27/05/2015.

Giá/m² = dự đoán VND / diện tích ở m². Giá/m² thật không thuộc đầu vào học máy vì được tính từ nhãn giá bán. TreeSHAP giải thích trên thang **log(1 + USD)**; các thanh không phải các khoản VND cộng riêng và không chứng minh quan hệ nhân quả.

Giao dịch đối chiếu đến từ train + validation, phải bán trước ngày định giá và khác mã căn nhà. Chúng giúp kiểm tra mặt bằng giá, không phải công thức tính của XGBoost.

## Trường học và cửa hàng

CSV gốc không có các tiện ích này. Đã thử Overpass, ohsome và tệp NCES 2013–2014 nhưng chưa truy xuất được snapshot phù hợp: timeout hoặc HTTP 403. **Không có khoảng cách hoặc nhận định gần trường/cửa hàng nào được điền giả. Mô hình hiện tại không dùng các biến này.**

`scripts/fetch_kingcounty_context.py` và adapter trong `backend/kingcounty.py` hỗ trợ snapshot OSM trước kỳ giao dịch. Khi có dữ liệu, phải kiểm tra nguồn, checksum, thời điểm và giấy phép trước khi so sánh thêm đặc trưng bằng validation trên một thiết kế đánh giá mới. Khoảng cách đường chim bay không xác định quyền tuyển sinh hoặc thời gian đi bộ.

## API và database

| Đường dẫn | Nội dung |
|---|---|
| GET `/api/kingcounty/info` | Metadata, nguồn tỷ giá và ví dụ test |
| POST `/api/kingcounty/predict` | Kiểm tra đầu vào, định giá, giải thích và lưu lịch sử |
| GET `/api/kingcounty/history` | 10 dự đoán gần nhất |
| GET `/evidence/<name>.png` | Biểu đồ được phép phục vụ |
| GET `/legacy` | Giao diện nhập dữ liệu cũ |

`kingcounty_sales` lưu giao dịch bằng mã căn và ngày bán, giá USD gốc và VND quy đổi cùng tỷ giá. `kingcounty_predictions` lưu đầu vào, đầu ra và phiên bản model. `real_estate_records` của bản cũ được giữ nguyên. Không đưa giá mô hình dự đoán vào nhãn huấn luyện.

## Tài liệu và artifact

- `docs/Thuyet_trinh_TieuLuan_CuoiKy.pptx`: 19 slide, có bảng và biểu đồ native chỉnh sửa được.
- `docs/Bao_cao_Phan_tich_Gia_nha_King_County.docx`: báo cáo phân tích, phương pháp, biểu đồ và ví dụ cụ thể.
- `docs/Phan_tich_Gia_nha_King_County.md`: nội dung báo cáo dạng Markdown.
- `artifacts/kingcounty/model.joblib`, `metadata.json`, `split.json`, `test_predictions.csv`, `evidence.json`: đối chiếu mô hình, điểm số và biểu đồ.
- Notebook mục 1–4 giữ thí nghiệm tham chiếu cũ; mục 5 là bản tích hợp mở rộng.

Các bản tài liệu cũ được sao lưu tại `.tools/kingcounty-20261107/backup` trong workspace. Không nạp joblib từ nguồn không tin cậy.

## Docker

Dockerfile đã bổ sung dataset, snapshot tỷ giá, biểu đồ và bước huấn luyện khi build. Image GHCR phát hành trước thay đổi này vẫn là bản cũ. Chưa build hoặc phát hành image mới trong lần cập nhật này.

```powershell
docker build -f TieuLuan_CuoiKy/deploy/Dockerfile -t python-k18-kingcounty TieuLuan_CuoiKy/real_estate_ai
docker run --rm -p 8000:8000 -v kingcounty-data:/app/storage python-k18-kingcounty
```

Nguồn: [Kaggle](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction), [GeoDa](https://geodacenter.github.io/data-and-lab/KingCounty-HouseSales2015/), [Vietcombank](https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-tien-ich/Ty-gia), [OpenStreetMap](https://www.openstreetmap.org/copyright).
