# Database cục bộ

Khi chọn SQLite, ứng dụng ghi dữ liệu vào `real_estate.db` trong thư mục này. UI và pipeline sử dụng chung file đó. Đây là dữ liệu khi chạy ứng dụng, được Git bỏ qua.

PostgreSQL lưu dữ liệu trên máy chủ theo `.env`, không lưu file database ở đây. Đổi backend không tự chuyển dữ liệu giữa hai database.
