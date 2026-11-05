# Notebook phân tích

Mở `TeamWork_PP_Nhom8.ipynb` bằng VS Code/Jupyter và chọn kernel `../real_estate_ai/.venv/Scripts/python.exe`.

Dataset King County nằm tại `../real_estate_ai/data/raw/kc_house_data.csv`. Notebook tự tìm đường dẫn từ thư mục notebook, thư mục dự án hoặc thư mục gốc repository. Giá trong notebook là USD; notebook không ghi đè mô hình VND của ứng dụng.

Cài thư viện bổ sung từ thư mục `TieuLuan_CuoiKy/real_estate_ai`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/notebook.txt
```

Các công cụ tạo/chạy notebook nằm trong `../scripts/`. Công cụ `build_teamwork_notebook.py` tạo lại toàn bộ nội dung; chỉ dùng khi chủ động muốn ghi đè các chỉnh sửa trong notebook.
