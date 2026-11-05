# Giao diện web

- `templates/index.html`: bố cục trang và các trường nhập liệu.
- `static/app.css`: màu sắc, bố cục và hiển thị trên điện thoại.
- `static/app.js`: xử lý tương tác và gọi `/api/*` bằng `fetch`.
- `static/house.svg`: biểu tượng ứng dụng.

Flask trong `../backend/web_app.py` phục vụ các file này. Mở bằng `TieuLuan_CuoiKy/chay_ui.cmd`; không mở HTML trực tiếp vì trang cần gọi API.
