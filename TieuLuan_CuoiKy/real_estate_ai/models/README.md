# Mô hình đã huấn luyện

Mô hình **chính King County** nằm tại `../artifacts/kingcounty/model.joblib`, kèm metadata, split, test predictions và biểu đồ. Huấn luyện bằng `python -m backend.train_kingcounty`. Mô hình học nhãn USD, giao diện hiển thị VND theo snapshot tỷ giá và ghi rõ thị trường Mỹ lịch sử.

Phần dưới là mô hình của công cụ cũ tại `/legacy`.

`house_model.pkl` và `house_model.metrics.json` được tạo ở đây sau khi huấn luyện đủ ít nhất 50 căn có giá bán thực hợp lệ. Các file sinh ra được Git bỏ qua.

API và pipeline cùng đọc mô hình VND này. Notebook King County dùng USD và không ghi mô hình vào thư mục này.
