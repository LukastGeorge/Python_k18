# Tiểu luận cuối kỳ — Demo xử lý giá nhà

Chương trình gồm nhập dữ liệu, làm sạch, dự đoán, lưu PostgreSQL và huấn luyện XGBoost. Phiên bản hiện tại chạy hai tin **DEMO**; chưa kết nối website thu thập tin thật. Giá có đơn vị VND, diện tích m².

## Giao diện web và API

Nhấp đúp **[chay_ui.cmd](../chay_ui.cmd)** ở thư mục `TieuLuan_CuoiKy` để mở giao diện tại **http://127.0.0.1:8000** với SQLite; dữ liệu lưu trong `storage/real_estate.db`. Không cần bật PostgreSQL hay kích hoạt môi trường của Lab1. Nếu thiếu Flask, chạy `../scripts/cai_dat.cmd` trước. Hoặc mở PowerShell từ thư mục gốc repository:

```powershell
cd E:\Workspace\Python_k18\TieuLuan_CuoiKy\real_estate_ai
.\.venv\Scripts\python.exe -m backend.web_app --backend sqlite --open-browser
```

UI gồm nhập thông tin nhà, dự đoán và lưu, nạp hai tin mẫu, thống kê, tìm kiếm, lọc và phân trang. Trang gọi JSON API bằng `fetch`; API dùng SQLAlchemy và bảng `real_estate_records` chung với pipeline. Chỉ API truy cập database; thông tin đăng nhập không gửi ra trình duyệt.

- **Minh họa:** gắn `is_demo=true`, dùng công thức minh họa khi chưa có mô hình. Các bản ghi không dùng huấn luyện và không nhận giá giao dịch thật.
- **Dữ liệu thật:** nhập tọa độ thực, có thể bổ sung giá giao dịch đã bán. Nếu chưa có mô hình VND, API lưu dữ liệu và trả `predicted_price=null`.
- Cùng mã căn nhà trong cùng chế độ sẽ cập nhật bản ghi hiện có. UI dùng nguồn `web` cho dữ liệu thật và `web_demo` cho minh họa; nút nạp mẫu dùng nguồn `demo` như pipeline.

Để dùng PostgreSQL, bật dịch vụ PostgreSQL, tạo database `GiaNha` nếu chưa có, điền đúng `.env`, rồi chạy:

```powershell
.\.venv\Scripts\python.exe -m backend.web_app --backend postgresql --open-browser
```

`--backend` chỉ áp dụng cho tiến trình đang chạy; không sửa `.env` và không tự chuyển dữ liệu giữa SQLite/PostgreSQL. Bỏ tham số này để đọc `DB_BACKEND` từ môi trường hoặc `.env`. UI vẫn mở khi database lỗi và hiển thị hướng dẫn kết nối. Giữ terminal mở; Ctrl+C để dừng. Nếu cổng 8000 đang dùng, thêm `--port 8001`.

API cùng địa chỉ với UI:

| Phương thức | Đường dẫn | Chức năng |
|---|---|---|
| GET | `/api/status` | Kiểm tra database, số bản ghi và mô hình VND |
| GET | `/api/records?page=1&page_size=10&q=&mode=all` | Danh sách; `mode` nhận `all`, `demo`, `real` |
| POST | `/api/records` | Kiểm tra đầu vào, dự đoán và lưu/cập nhật |
| POST | `/api/demo` | Nhận `{}`, cập nhật hai tin mẫu không tạo bản ghi trùng |

Ví dụ gọi API trong một PowerShell khác khi web đang chạy:

```powershell
$body = @{
    mode = "demo"
    id = "API-001"
    title = "Demo nha 50 m2"
    area = 50
    rooms = 2
    latitude = 10.762622
    longitude = 106.660172
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/records" -Method Post -ContentType "application/json" -Body $body
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/records"
```

API trả JSON với HTTP 400 khi dữ liệu sai, 415 khi thiếu kiểu JSON, 503 khi không thao tác được database. Với `mode=real`, `actual_price` là số VND hoặc bỏ trống; API tự gán `price_kind=sale` khi có giá. Phạm vi số dùng chung với pipeline ở bên dưới. Web chỉ lắng nghe trên máy hiện tại (`127.0.0.1`), dành cho chạy và demo cục bộ; chưa có đăng nhập/phân quyền cho triển khai công khai. API tham chiếu [Flask Quickstart](https://flask.palletsprojects.com/en/stable/quickstart/) và [kiểm thử Flask](https://flask.palletsprojects.com/en/stable/testing/).

## Chạy trên máy này

Nhấp đúp **[scripts/chay_demo.cmd](../scripts/chay_demo.cmd)** để chạy một lần. Hoặc mở PowerShell:

Từ thư mục gốc repository `Python_k18`:

```powershell
cd .\TieuLuan_CuoiKy\real_estate_ai
.\.venv\Scripts\python.exe -m backend.run_hourly --once
```

Môi trường riêng nằm trong `.venv` của thư mục này. Không dùng nhầm Python mặc định hoặc `.venv-src` của các bài khác. Trong VS Code, chọn **Python: Select Interpreter → Enter interpreter path**, rồi chọn `.venv/Scripts/python.exe` của demo này.

`../scripts/chay_theo_gio.cmd` chạy ngay và lặp sau mỗi 60 phút; phải giữ terminal mở, Ctrl+C để dừng. Đây là vòng lặp trong chương trình, chưa cài dịch vụ Windows hay lịch tự chạy khi bật máy.

```powershell
.\.venv\Scripts\python.exe -m backend.run_hourly
.\.venv\Scripts\python.exe -m backend.run_hourly --interval 5
```

## Kết nối database

`.env` lưu cấu hình hiện tại: PostgreSQL, host 127.0.0.1, cổng 5432, database GiaNha. Mật khẩu nằm riêng trong `.env`; file này và `.venv` được Git bỏ qua. Cấu hình mẫu ở `.env.example`. Các script cùng sử dụng `backend/config.py` và `URL.create`, nên mật khẩu chứa ký tự đặc biệt không phá chuỗi kết nối.

Database GiaNha cần tồn tại trước. Chương trình tự tạo **bảng real_estate_records**. Bảng cũ `real_estate_prices`, nếu có, được giữ nguyên vì thiếu cờ phân biệt demo/giá thực và có thể đã chứa các tin lặp. Trong pgAdmin, mở **GiaNha → Schemas → public → Tables → real_estate_records**, refresh danh sách nếu chưa thấy.

Để chạy khi không có PostgreSQL, đổi `DB_BACKEND=sqlite` trong `.env`. Khi đó dữ liệu nằm ở `storage/real_estate.db` trong thư mục dự án. Đây là lựa chọn chủ động; chương trình không âm thầm chuyển database khi PostgreSQL bị lỗi.

## Demo hiện làm gì

1. Đọc hai tin mẫu, có tọa độ mẫu gắn rõ `is_demo=true`.
2. Chuyển diện tích `50m2`, `75 m²` hoặc số sang m²; kiểm tra phòng ngủ và tọa độ.
3. Nếu chưa có mô hình, chỉ dữ liệu demo được dùng công thức minh họa: diện tích × 40 triệu + số phòng ngủ × 50 triệu VND.
4. Lưu `prediction_method=demo_formula` và `actual_price=NULL`. Hai kết quả mẫu là 2,10 tỷ và 3,15 tỷ VND; không phải giá thị trường được xác minh.
5. Lưu/cập nhật theo khóa `(source, id)`. Chạy lại hai tin demo vẫn chỉ có hai dòng thuộc nguồn demo.

Nếu có mô hình đã huấn luyện hợp lệ, pipeline nạp lại mô hình ở mỗi lần chạy. File hỏng hoặc sai cấu trúc được báo lỗi, không bị che bằng mô hình giả.

## Nhập dữ liệu thật

Điền CSV UTF-8 theo header trong `data/input/input_template.csv`. Mỗi tên cột chỉ xuất hiện một lần. Mỗi dòng là một căn nhà có ID ổn định trong nguồn; không để trùng ID. Mã như `NA`, `NULL` và số 0 ở đầu được giữ nguyên. Tên nguồn được bỏ khoảng trắng hai đầu và không được để trống. Trường bắt buộc:

| Cột | Ý nghĩa |
|---|---|
| id, title | Mã căn nhà và tiêu đề; không để trống |
| area | Diện tích m², từ 10 đến 1.000 |
| rooms | Số phòng ngủ nguyên từ 0 đến 30 |
| latitude, longitude | Tọa độ thật; không tự điền tọa độ mẫu cho CSV |
| actual_price | Giá bán thực bằng số VND; để trống khi chưa biết |
| price_kind | `sale` khi có giá bán thực; `unknown` khi chưa biết |

Giá bán thực nếu cung cấp phải từ 100 triệu đến 500 tỷ VND. Đây là giới hạn demo, không phải quy tắc xác định tin giả. Không đưa giá rao hoặc giá mô hình đoán vào actual_price. Mỗi nguồn chỉ nhập dữ liệu nhất quán về phạm vi địa lý và đơn vị.

```powershell
.\.venv\Scripts\python.exe -m backend.data_pipeline --csv "data\input\du_lieu_that.csv" --source "nguon_cua_toi"
```

Nếu chưa có mô hình, dữ liệu thật vẫn được lưu với `predicted_price=NULL`; không dùng công thức demo để gán giá thật. Dùng cùng source và ID ở lần nhập sau sẽ cập nhật dòng hiện có. CSV là bản ghi đầy đủ cho mỗi căn: một giá trị trống trong lần nhập mới sẽ thay giá trị cũ của trường đó.

## Huấn luyện

```powershell
.\.venv\Scripts\python.exe -m backend.retrain_model
```

Hoặc nhấp đúp `../scripts/huan_luyen.cmd`. Chương trình chỉ đọc các dòng `is_demo=false`, `price_kind=sale`, có actual_price, và cần ít nhất **50 căn hợp lệ sau làm sạch**. Hai tin demo chạy bao nhiêu lần cũng không đủ điều kiện huấn luyện.

Chia ngẫu nhiên 80/20 với seed 42, huấn luyện XGBoost bằng actual_price, báo MAE, RMSE, R² và MAE baseline. `models/house_model.pkl` chứa mô hình, thứ tự đặc trưng, đơn vị giá và kết quả kiểm thử. Mô hình lưu là bản chỉ học train để điểm test có thể đối chiếu. `models/house_model.metrics.json` chứa các chỉ số.

Thiếu dữ liệu thì chương trình báo rõ và giữ mô hình hiện có. Đây chưa phải đánh giá dự báo tương lai: chưa có ngày giao dịch để chia theo thời gian, và ID cần thực sự đại diện căn nhà, không phải mỗi tin đăng lại. Chưa có mô hình thật được tạo chỉ từ hai tin demo.

## Cài trên máy khác

Khuyến nghị Python 3.12; nhấp đúp `../scripts/cai_dat.cmd` hoặc chạy:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/base.txt
Copy-Item .env.example .env
```

Chỉ sao chép `.env.example` khi chưa có `.env`; sau đó điền mật khẩu của máy đó. `requirements/base-lock.txt` ghi phiên bản đã kiểm tra trên máy này.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Kiểm thử dùng SQLite tạm và dữ liệu giả lập riêng trong thư mục tạm, không ghi fixture vào PostgreSQL GiaNha. Có kiểm tra nhập lặp, đầu vào sai, mô hình hỏng, không học nhãn demo, đủ mẫu sau lọc, nhập CSV → train → nạp mô hình → dự đoán và lịch chạy một lần.

Các tài liệu API tham chiếu: [SQLAlchemy upsert](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert), [XGBoost Python API](https://xgboost.readthedocs.io/en/stable/python/python_api.html#xgboost.XGBRegressor).

## Notebook bàn giao nhóm 8

File [TeamWork_PP_Nhom8.ipynb](../notebooks/TeamWork_PP_Nhom8.ipynb) nằm trong `TieuLuan_CuoiKy/notebooks`.
Notebook có nguồn và mô tả dataset, kiểm tra dữ liệu bằng NumPy/Pandas, ba biểu đồ khám phá,
so sánh Ridge/XGBoost với baseline, chia theo mã nhà và đánh giá MAE/RMSE/R².

Dataset công khai **House Sales in King County, USA** có 21.613 giao dịch, 21 thuộc tính,
giai đoạn 2014–2015. CSV đã tải tại `data/raw/kc_house_data.csv`; nguồn và checksum ở
`data/raw/king_county_source.json`. Giá trong notebook là **USD**, diện tích được đổi từ ft² sang m².
Notebook dùng bốn đầu vào của demo nhưng chạy độc lập, không cần PostgreSQL và không ghi đè
`models/house_model.pkl` hay nhập giá USD vào database VND.

Cài thêm thư viện tại thư mục `real_estate_ai`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/notebook.txt
```

Mở notebook trong VS Code (tiện ích Jupyter), chọn kernel `.venv` của `real_estate_ai`,
rồi chọn **Restart Kernel and Run All**. Có thể xem kết quả đã lưu mà không cần chạy lại.
Khi gửi riêng notebook sang máy khác, cần cài các thư viện nêu trong notebook và có Internet
để tải CSV; gửi kèm `real_estate_ai/data/raw/kc_house_data.csv` để chạy không cần tải lại.
