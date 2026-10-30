# Phân tích bất động sản và dự đoán giá nhà

Tiểu luận Lập trình Python, lớp 020100138002. **Nhóm 8 – cá nhân Nguyễn Duy Trường, MSSV 24150180, STT 6**. Ngành Công nghệ thông tin, chuyên ngành Kỹ thuật phần mềm. Giảng viên: ThS. Lý Ngọc Hưng.

Ứng dụng dùng dữ liệu giao dịch nhà ở Ames, Iowa (Mỹ), giai đoạn 2006–2010 để phân tích giá và dự đoán từ 15 thuộc tính. Giá là USD, diện tích là ft². Mô hình phục vụ minh họa học máy trong phạm vi dữ liệu này.

## Chạy ứng dụng

Khuyến nghị Python 3.12. Tại thư mục dự án, chạy PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Mở địa chỉ hiển thị trong terminal, mặc định http://127.0.0.1:8501. Dừng bằng Ctrl+C. Nếu máy đã có môi trường `.venv` được chuẩn bị trong dự án, chỉ cần chạy lệnh cuối. Không cần kích hoạt môi trường bằng Activate.ps1. Nếu dùng Python khác, cần cài thư viện tương thích rồi huấn luyện lại mô hình trước khi chạy.

Mô hình, dữ liệu và các hình đã được đóng gói; chạy demo không cần tải lại dataset. Sau lần cài thư viện, các chức năng chính hoạt động ngoại tuyến.

## Tái lập toàn bộ kết quả

```powershell
.\.venv\Scripts\python.exe -m scripts.train
.\.venv\Scripts\python.exe -m scripts.visualize
.\.venv\Scripts\python.exe -m pytest -q
```

Huấn luyện có seed 42. Chia train/test 80/20; so sánh Median baseline, Linear Regression, Random Forest và Gradient Boosting. Chọn mô hình bằng RMSE kiểm định chéo 5 phần trên train. MAE, RMSE và R² trên test chỉ dùng đánh giá cuối. Phiên bản thư viện, mã SHA-256 dữ liệu và cấu hình nằm trong `artifacts/metadata.json`.

Pipeline học trung vị/mốt, phân vị cắt ngọn 1%/99%, tham số chuẩn hóa và mã hóa từ dữ liệu train của từng fold. Không điền thiếu hoặc chuẩn hóa trên toàn bộ dataset trước khi chia. Mô hình lưu trong `model.joblib` là bản fit trên train, đúng bản được đánh giá trong báo cáo. Chỉ nạp tệp joblib đi kèm dự án hoặc tệp do chính mình huấn luyện.

## Cấu trúc

```text
app.py                       Ứng dụng Streamlit tiếng Việt
src/housing.py               Tiền xử lý và kiểm tra dữ liệu dự đoán
scripts/train.py             Huấn luyện, đánh giá và lưu mô hình
scripts/visualize.py         Tạo 7 hình phân tích
tests/test_project.py        Kiểm thử dữ liệu, mô hình và giao diện
data/raw/                   Dữ liệu gốc TSV, CSV và từ điển biến
data/processed/housing.csv   Dữ liệu chọn thuộc tính, chưa điền thiếu
data/sample_input.csv        10 căn nhà để thử dự đoán theo lô
artifacts/                  Mô hình, kết quả, phân chia dữ liệu, hình
docs/                       Báo cáo Word/PDF và hướng dẫn bảo vệ
requirements.txt            Thư viện trực tiếp, khóa phiên bản
requirements-lock.txt       Toàn bộ phiên bản đã dùng
```

## Dữ liệu đầu vào

Đầu vào gồm diện tích đất, diện tích ở, chất lượng, tình trạng, năm xây/cải tạo, phòng ngủ, phòng tắm, chỗ đỗ xe, diện tích gara/tầng hầm, khu vực, loại nhà, kiểu nhà và điều hòa. Tên cột CSV dùng đúng `data/sample_input.csv`. Giới hạn 2.000 dòng và 4 MB. Số bị thiếu được pipeline điền; thiếu cột, chuỗi không phải số, số vô hạn, số âm ngoài miền, mã khu vực lạ và năm cải tạo trước năm xây bị từ chối.

1 ft² = 0,09290304 m². Khi nhập diện tích tính bằng m², chia cho 0,09290304 để đổi sang ft². Không đổi nhãn USD thành VNĐ vì như vậy không tạo được mô hình cho thị trường Việt Nam.

## Nguồn và phạm vi

- De Cock, D. (2011). *Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project*. Journal of Statistics Education, 19(3). https://doi.org/10.1080/10691898.2011.11889627
- Dữ liệu gốc: https://jse.amstat.org/v19n3/decock/AmesHousing.txt
- Từ điển biến: https://jse.amstat.org/v19n3/decock/DataDocumentation.txt
- Phòng tránh rò rỉ dữ liệu: https://scikit-learn.org/stable/common_pitfalls.html
- Kiểm thử ứng dụng: https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest

Dataset được tác giả công bố phục vụ học tập/nghiên cứu; giữ nguồn và các tài liệu đi kèm khi chia sẻ. Dữ liệu không đại diện thị trường Việt Nam hoặc giá hiện tại. Phân chia ngẫu nhiên đánh giá nội suy trong cùng thị trường/giai đoạn; để dự báo tương lai cần dữ liệu mới và đánh giá theo thời gian. Độ quan trọng và tương quan không chứng minh quan hệ nhân quả.

## Hồ sơ nộp và lịch

Đăng ký đề tài với giảng viên trước 20/10/2026; nộp báo cáo, link dự án và dataset ngày 05/11/2026. Nhóm 8 báo cáo ngày 06/11/2026. Báo cáo cá nhân đặt tên theo STT 6, họ tên và MSSV.

Toàn bộ sản phẩm được chuẩn bị tại máy. Xem `docs/HUONG_DAN_NOP_BAI.md` để đưa dự án lên GitHub và nộp qua kênh giảng viên cung cấp.
