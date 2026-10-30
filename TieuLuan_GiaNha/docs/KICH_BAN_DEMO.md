# Demo phiên bản dữ liệu Mỹ 2016–2026

1. Chạy `chay_demo.cmd`, mở Tổng quan. Nói rõ mục tiêu 51 khu vực nhưng dữ liệu hiện tại chỉ gồm Boulder County (Colorado) và Washington, D.C., 48.584 giao dịch.
2. Vào Độ phủ 51 khu vực. Chỉ ra 49 bang chưa có dữ liệu và sự khác nhau giữa có mẫu với đầy đủ dữ liệu. Năm 2026 chưa hoàn tất.
3. Khám phá dữ liệu: chọn hai khu vực để chồng đường giá trung vị theo tháng; lọc giai đoạn, xem phân phối giá và xuất CSV.
4. Dự đoán giá nhà: chọn Colorado/Boulder County hoặc D.C.; nhập diện tích, phòng ngủ, phòng tắm, năm xây, tháng/năm. Chuyển m²/ft² và giải thích định nghĩa diện tích riêng của nguồn.
5. Chọn California để minh họa ứng dụng chặn dự đoán ở bang thiếu dữ liệu. Chọn lại D.C. và thử dự đoán bình thường.
6. Chọn nhập CSV, dùng data/us_sample_input.csv. Giải thích đây là mẫu thao tác, không phải tập kiểm thử độc lập.
7. Đánh giá mô hình: train 2016–2023, validation 2024, test 2025–2026. Loại giao dịch cũ của căn nhà thuộc tập giữ lại. Chọn bằng validation, chỉ đánh giá cuối trên test.
8. Nêu MAE khoảng 266 nghìn USD, RMSE khoảng 521 nghìn USD, R² 0,686. Sai số cao nên cần bổ sung vị trí chi tiết và đặc điểm nhà trước khi dùng thực tế.

## Câu hỏi cần nắm

**Tại sao là 51?** 50 bang và Washington, D.C.; D.C. không phải bang thứ 51.

**Tại sao không dùng Zillow ZHVI để dự đoán giá từng căn?** Đó là giá nhà điển hình theo khu vực. Không phải nhãn giao dịch cho một căn có diện tích/số phòng xác định.

**Tại sao không lấy price + prev_sold_date từ tin rao?** Giá rao hiện tại không nhất thiết là giá của lần bán trước. Ghép hai trường đó có thể tạo lịch sử giá sai.

**Dữ liệu hiện tại có đủ toàn quốc không?** Chưa. Chỉ có mẫu thuộc hai khu vực, Colorado mới có một quận. 49 bang còn lại được báo thiếu rõ ràng.

**Dữ liệu đặc điểm có đúng tại lúc bán không?** Chưa xác nhận. Đây là snapshot hiện tại của cơ quan thuế. Có lọc năm xây/cải tạo quá ngày bán, nhưng vẫn còn nguy cơ thông tin tương lai và thiên lệch do chỉ còn tài sản hiện hành.

**Vì sao tách theo thời gian và mã căn nhà?** Đánh giá các năm sau, đồng thời tránh cho cùng căn nhà với giá bán khác năm xuất hiện ở cả train và test.

**Vì sao hai file mô hình?** evaluation_model.joblib giữ bản đánh giá chưa học test. model.joblib phục vụ demo đã được fit lại bằng toàn bộ dữ liệu để tận dụng thông tin mới; điểm test chỉ thuộc bản đánh giá.

**Giá trị R² 0,686 có nghĩa dự đoán đúng 68,6% không?** Không. R² so sánh sai số bình phương với mô hình dự đoán trung bình; MAE và RMSE thể hiện sai số USD.

**Làm sao thêm một bang?** Tìm nguồn công khai có giá bán gắn đúng ngày, đặc điểm và mã tài sản. Viết adapter, khai báo nguồn/định nghĩa diện tích, kiểm tra độ phủ, huấn luyện lại và kiểm thử. Thêm tên bang không tạo ra dữ liệu.
