# Chuẩn bị nộp bài

## Các tệp cần nộp

- Báo cáo `6_Nguyễn Duy Trường_24150180.docx` trong `docs/`; có thể xuất PDF từ Word sau khi xem lại.
- Link repository GitHub/GitLab mà giảng viên truy cập được.
- Database `data/us_housing.sqlite3`, `data/raw/us/manifest.json`, bảng độ phủ và `docs/DU_LIEU_MY_2016_2026.md`. Nguồn gốc ở `data/raw/us/`; ghi rõ dữ liệu mới có hai khu vực.
- Khi demo: mã nguồn, `artifacts/`, thư viện và ứng dụng đã chạy thử.

## Đưa dự án lên GitHub

Tạo repository mới trên tài khoản của mình. Đưa các tệp trong dự án lên, gồm dữ liệu và mô hình; loại `.venv`, `.buildtmp`, cache và log theo `.gitignore`. Không tải toàn bộ môi trường Python.

Nếu dùng GitHub CLI, đăng nhập trước bằng `gh auth login`. Sau khi đã xem lại nội dung và chọn tên/quyền truy cập repository, có thể dùng giao diện GitHub hoặc các lệnh `git init`, `git add`, `git commit`, thêm remote rồi `git push`. Nếu chọn private, cấp quyền cho giảng viên theo yêu cầu của lớp.

Mở thử đường link từ phiên đăng nhập phù hợp để kiểm tra khả năng truy cập. Chỉ đưa link thật đã kiểm tra vào biểu mẫu nộp bài; không sử dụng đường dẫn thư mục trên máy như link dự án.

## Các mốc

- Trước 20/10/2026: thông báo đề tài đã chọn cho giảng viên.
- 05/11/2026: hạn nộp báo cáo, link dự án và dataset.
- 06/11/2026: nhóm 8 báo cáo; có mặt và ký danh sách dự thi.

File ZIP là bản sao để bàn giao/giải nén. Khi thay đổi mã nguồn hoặc báo cáo, tạo lại ZIP để tránh nộp phiên bản cũ.

