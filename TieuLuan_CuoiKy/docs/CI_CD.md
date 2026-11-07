# CI và xuất bản Docker image

Workflow: [TieuLuan CuoiKy CI CD](https://github.com/LukastGeorge/Python_k18/actions/workflows/tieuluan-cuoiky.yml).

Image: `ghcr.io/lukastgeorge/python-k18-cuoiky`.

## Quy trình tự động

Khi push vào `main` hoặc tạo/cập nhật pull request vào `main` có thay đổi trong `TieuLuan_CuoiKy`, GitHub Actions thực hiện:

1. Kiểm tra cú pháp JavaScript của giao diện.
2. Build image Linux AMD64 với Python 3.12, thư viện ứng dụng và Waitress.
3. Chạy toàn bộ pytest ngay bên trong image. SQLite dùng file tạm; bài tích hợp PostgreSQL dùng dịch vụ PostgreSQL 17 và schema riêng, tự xóa sau kiểm thử.
4. Kiểm tra checksum dataset King County.
5. Chạy container mới, kiểm tra UI, file CSS/JS, kết nối SQLite, nhập dữ liệu, cập nhật tin mẫu không trùng, lọc và từ chối đầu vào sai. Kiểm tra thư viện ML nạp được trong container.
6. Lưu kết quả kiểm thử và log ở mục Artifacts của lần chạy.

Sau khi CI đạt trên `main`, job CD tải đúng image vừa kiểm thử, đối chiếu image ID rồi xuất bản hai tag:

- `latest`: bản mới nhất đã vượt qua kiểm tra.
- `sha-<commit đầy đủ>`: bản gắn với một commit cụ thể.

CD không build lại image. Pull request chỉ kiểm thử và không xuất bản. Có thể chạy lại bằng nút **Run workflow** tại trang Actions, chọn nhánh `main`.

Quyền ghi package chỉ được cấp cho job xuất bản; đăng nhập GHCR dùng `GITHUB_TOKEN` của lần chạy. Các action bên ngoài được cố định bằng commit SHA. Tham khảo [hướng dẫn xuất bản Docker của GitHub](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images).

## Chạy image trên máy

Mở Docker Desktop với Linux containers. Từ thư mục gốc repository `Python_k18`, chạy PowerShell:

```powershell
docker compose -f TieuLuan_CuoiKy/deploy/compose.yaml pull
docker compose -f TieuLuan_CuoiKy/deploy/compose.yaml up -d
```

Mở **http://127.0.0.1:8000**. Nếu cổng 8000 đang được chương trình khác sử dụng, đặt cổng khác trước khi chạy Compose:

```powershell
$env:UI_PORT = "8001"
docker compose -f TieuLuan_CuoiKy/deploy/compose.yaml up -d
```

Sau đó mở http://127.0.0.1:8001.

Nếu package đang private, đăng nhập `ghcr.io` bằng tài khoản có quyền đọc package trước khi pull. Dùng token có quyền `read:packages` qua `docker login --password-stdin`; không lưu token trong mã nguồn. Xem [xác thực với Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry#authenticating-to-the-container-registry).

Đọc log và dừng ứng dụng:

```powershell
docker compose -f TieuLuan_CuoiKy/deploy/compose.yaml logs -f app
docker compose -f TieuLuan_CuoiKy/deploy/compose.yaml down
```

## Database và mô hình

Image mặc định dùng SQLite. Database trong container nằm tại `/app/storage/real_estate.db`, được Compose lưu bằng named volume `cuoiky-data`. Volume `cuoiky-models` dành cho mô hình VND tại `/app/models`. Các volume được giữ khi dừng bằng `compose down`.

Database Docker độc lập với file `real_estate_ai/storage/real_estate.db` đang dùng khi chạy `chay_ui.cmd`; dữ liệu không được tự chuyển giữa hai cách chạy. Image không chứa `.env`, database cá nhân, file mô hình, notebook hoặc báo cáo. Các bản ghi smoke test nằm ở container kiểm thử bị xóa sau CI, không nằm trong image xuất bản.

Để dùng PostgreSQL, cấu hình các biến `DB_BACKEND=postgresql`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` khi chạy container. `DB_HOST` phải là máy chủ mà container truy cập được; `127.0.0.1` trong container chỉ chính container đó.

Waitress phục vụ WSGI trong container; lệnh `chay_ui.cmd` cục bộ tiếp tục dùng cách chạy Flask hiện có. Cách nạp app factory bằng Waitress theo [tài liệu Flask](https://flask.palletsprojects.com/en/stable/deploying/waitress/).

## Chọn phiên bản và build thủ công

Để chạy lại một commit đã xuất bản:

```powershell
$env:CUOIKY_IMAGE = "ghcr.io/lukastgeorge/python-k18-cuoiky:sha-<commit đầy đủ>"
docker compose -f TieuLuan_CuoiKy/deploy/compose.yaml pull
docker compose -f TieuLuan_CuoiKy/deploy/compose.yaml up -d
```

Build image từ mã nguồn hiện tại:

```powershell
docker build -f TieuLuan_CuoiKy/deploy/Dockerfile -t cuoiky-local TieuLuan_CuoiKy/real_estate_ai
```

`scripts/smoke_container.py` chỉ dành cho container kiểm thử mới, rỗng; script ghi dữ liệu giả lập để kiểm tra API. Không chạy script này với database đang sử dụng.

Phạm vi CD hiện tại là xuất bản image trên GHCR theo lựa chọn bàn giao; chưa tự chạy ứng dụng trên VPS/hosting hay cung cấp một URL UI online. Compose mặc định chỉ mở cổng trên máy hiện tại. `WEB_TRUSTED_HOSTS` cho phép cấu hình danh sách hostname hợp lệ khi thay đổi môi trường chạy.
