# Tiểu luận cuối kỳ — Dự đoán giá nhà

## Mở chương trình

Nhấp đúp **[chay_ui.cmd](chay_ui.cmd)** ngay trong thư mục này. Giao diện mở tại **http://127.0.0.1:8000**, dùng SQLite và lưu dữ liệu trong `real_estate_ai/storage/real_estate.db`. Giữ terminal mở; Ctrl+C để dừng.

Máy chưa cài thư viện: chạy **[scripts/cai_dat.cmd](scripts/cai_dat.cmd)** trước. Khuyến nghị Python 3.12.

## Tìm file cần chỉnh sửa

| Bạn cần làm gì? | Vị trí |
|---|---|
| Sửa giao diện HTML | `real_estate_ai/frontend/templates/index.html` |
| Sửa màu sắc, bố cục | `real_estate_ai/frontend/static/app.css` |
| Sửa tương tác UI, gọi API | `real_estate_ai/frontend/static/app.js` |
| Sửa API và web server | `real_estate_ai/backend/web_app.py` |
| Sửa kết nối database, đường dẫn | `real_estate_ai/backend/config.py` |
| Sửa cấu trúc bảng và truy vấn | `real_estate_ai/backend/database.py` |
| Sửa nhập liệu và làm sạch | `real_estate_ai/backend/data_pipeline.py`, `validation.py` |
| Sửa huấn luyện và dự đoán | `real_estate_ai/backend/retrain_model.py`, `model_inference.py` |
| Chỉnh cấu hình PostgreSQL/SQLite | `real_estate_ai/.env` — cấu hình mẫu: `.env.example` |
| Xem notebook phân tích | [notebooks/TeamWork_PP_Nhom8.ipynb](notebooks/TeamWork_PP_Nhom8.ipynb) |
| Xem báo cáo và tài liệu | [docs/](docs/) |

## Cấu trúc thư mục

```text
TieuLuan_CuoiKy/
├── README.md
├── chay_ui.cmd                    # Mở giao diện bằng SQLite
├── docs/                          # Báo cáo và tài liệu
├── notebooks/                     # Phân tích King County bằng USD
├── scripts/                       # Cài đặt, demo, chạy lịch, train, tạo notebook
└── real_estate_ai/
    ├── backend/                   # Mã Python: API, database, pipeline, mô hình
    ├── frontend/
    │   ├── templates/             # HTML
    │   └── static/                # CSS, JavaScript, SVG
    ├── data/
    │   ├── raw/                   # Dataset gốc + nguồn/checksum
    │   └── input/                 # Mẫu CSV và dữ liệu nhập cho pipeline
    ├── models/                    # Mô hình VND và chỉ số sau huấn luyện
    ├── storage/                   # Database SQLite khi chạy
    ├── requirements/              # Thư viện ứng dụng/notebook và bản khóa
    ├── tests/                     # Kiểm thử pipeline và API
    ├── .env                       # Cấu hình riêng, không đưa lên Git
    └── .venv/                     # Môi trường Python riêng, không đưa lên Git
```

## Công cụ khác

| Công cụ | Chức năng |
|---|---|
| `scripts/cai_dat.cmd` | Cài môi trường và thư viện ứng dụng |
| `scripts/chay_demo.cmd` | Chạy pipeline một lần theo database trong `.env` |
| `scripts/chay_theo_gio.cmd` | Chạy pipeline ngay và lặp mỗi 60 phút |
| `scripts/huan_luyen.cmd` | Huấn luyện mô hình VND khi đủ giá bán thật |
| `scripts/build_teamwork_notebook.py` | Tạo lại notebook; sẽ ghi đè notebook hiện có |
| `scripts/execute_teamwork_notebook.py` | Chạy và lưu lại toàn bộ kết quả notebook |

Xem [hướng dẫn ứng dụng và API](real_estate_ai/README.md) để chạy bằng PowerShell hoặc chuyển sang PostgreSQL. Các lệnh Python mới dùng `-m backend.<tên_module>` tại thư mục `real_estate_ai`.

Notebook King County dùng **USD** và chạy độc lập với database. UI/pipeline dùng **VND**; dữ liệu minh họa được tách riêng khỏi dữ liệu huấn luyện thật.
