# Lab 5 - Trực quan hóa dữ liệu với Python

Bài làm theo `Lab5_PP_Data_visualization.docx`, gồm đầy đủ ba nhiệm vụ Matplotlib và ba nhiệm vụ Seaborn. Các list dữ liệu được giữ nguyên như đề. Hai chương trình xuất tổng cộng sáu ảnh PNG ở 300 DPI, đồng thời in đường dẫn ảnh và kết quả phân tích ra terminal.

## Mã nguồn và dữ liệu

| File | Nội dung |
| --- | --- |
| `ex01_matplotlib.py` | Doanh số, ngân sách quảng cáo và lượng mưa theo 12 tháng năm 2025. |
| `ex02_seaborn.py` | Điểm thi, giờ học và chuyên ngành của 20 sinh viên; tính trung vị theo ngành. |
| `test_lab5.py` | Kiểm thử dữ liệu, thống kê, số điểm, nội dung và định dạng biểu đồ. |
| `requirements.txt` | Các thư viện cần cài cho Lab5. |

## Cách chạy bằng PowerShell

Môi trường riêng của Lab5 nằm tại `.venv`, dùng Python 3.14.4. Các phiên bản đã kiểm tra là Matplotlib 3.11.2, Seaborn 0.13.2 và SciPy 1.18.1, được cố định trong `requirements.txt`. Từ thư mục gốc dự án, chạy:

```powershell
Set-Location 'E:\Workspace\Python_k18'
.\Lab5\.venv\Scripts\python.exe -X utf8 Lab5\ex01_matplotlib.py
.\Lab5\.venv\Scripts\python.exe -X utf8 Lab5\ex02_seaborn.py
```

Chương trình không chờ nhập liệu. Các file PNG được lưu ngay trong `Lab5`, cạnh mã nguồn, dù bạn chạy lệnh từ thư mục nào. Mở ảnh trong VS Code, Codex hoặc ứng dụng xem ảnh để xem kết quả. Chạy lại sẽ cập nhật các ảnh cùng tên.

Khi chuyển bài sang máy khác, tạo lại môi trường và cài thư viện:

```powershell
Set-Location 'E:\Workspace\Python_k18'
python -m venv Lab5\.venv
.\Lab5\.venv\Scripts\python.exe -m pip install -r Lab5\requirements.txt
```

Mã dùng Matplotlib, Seaborn và SciPy cho KDE. NumPy, pandas và các phụ thuộc khác được trình cài đặt tự xử lý; dữ liệu đầu vào của bài vẫn là list/dictionary, không cần tự tạo DataFrame. Khi đóng gói bài, chỉ cần mã nguồn, README, requirements và ảnh kết quả; không cần đưa `.venv` vào ZIP.

## Các ảnh kết quả

| Bài và nhiệm vụ | File PNG | Nội dung |
| --- | --- | --- |
| 3.1 - Nhiệm vụ 1 | `xu_huong_doanhso_2025.png` | Doanh số theo tháng, đường `darkblue`, nét đứt, marker tròn. |
| 3.1 - Nhiệm vụ 2 | `chitieu_quangcao_2025.png` | Cột quảng cáo, tô `crimson` cho tháng cao nhất và thêm chú thích. |
| 3.1 - Nhiệm vụ 3 | `baocao_doanhso_2025.png` | Subplots 1×2: quảng cáo–doanh số và doanh số–lượng mưa theo tháng. |
| 3.2 - Nhiệm vụ 1 | `phanbo_diem_python.png` | Histogram 6 khoảng màu `teal` và đường KDE. |
| 3.2 - Nhiệm vụ 2 | `thoigian_hoc_va_diem.png` | Scatter giờ học–điểm, phân màu theo ngành bằng bảng `Set1`. |
| 3.2 - Nhiệm vụ 3 | `phantich_diem_seaborn.png` | Boxplot theo ngành, kèm nhãn trung vị và số sinh viên. |

Ảnh báo cáo doanh số có kích thước **3600 × 1200 pixel**, tương ứng Figure 12 × 4 inch ở 300 DPI. Năm ảnh còn lại có kích thước **2400 × 1350 pixel**, tương ứng 8 × 4,5 inch ở 300 DPI.

## Bài 3.1 - Phân tích doanh số

Nhiệm vụ 1 dùng `ax.plot()` với đúng màu, nét, marker, tiêu đề, nhãn trục và lưới của đề. Doanh số cao nhất vào T12 với **280 triệu VNĐ**, thấp nhất vào T1 với **120 triệu VNĐ**. Sau khi tăng từ T1 đến T6, doanh số giảm từ T7 đến T10 rồi tăng lại ở T11–T12.

Nhiệm vụ 2 dùng `max(ad_budget)` để tìm chi tiêu cao nhất: **T12, 35 triệu VNĐ**. Cột này có màu `crimson`, các cột còn lại là `skyblue`. Đề mô tả “xám skyblue”; mã dùng đúng tên màu `skyblue`, thực tế là xanh da trời. Chú thích được tạo bằng `ax.annotate()` và có mũi tên trỏ vào cột cao nhất.

Nhiệm vụ 3 tạo `plt.subplots(1, 2, figsize=(12, 4))`. Scatter cho thấy trong dữ liệu mẫu, các tháng chi nhiều quảng cáo thường có doanh số cao hơn. Biểu đồ theo tháng dùng trục Y trái cho doanh số (triệu VNĐ), trục Y phải cho lượng mưa (mm), có màu nhãn và chú thích tương ứng. Vì hai đại lượng khác đơn vị, không đọc độ chênh giữa hai đường như chênh lệch của cùng một đại lượng. Các hình mô tả dữ liệu quan sát, không chứng minh quảng cáo hay lượng mưa là nguyên nhân thay đổi doanh số.

## Bài 3.2 - Phân tích điểm thi

Cả ba hình Seaborn dùng chủ đề `whitegrid`. Histogram thể hiện số sinh viên trong mỗi khoảng điểm; đường KDE giúp nhìn dạng phân bố mịn hơn. Scatter có 20 điểm với màu chuyên ngành nhất quán giữa chú thích và boxplot.

Trung vị được tính bằng `statistics.median()` sau khi nhóm điểm bằng dictionary:

| Chuyên ngành | Số sinh viên | Trung vị điểm |
| --- | ---: | ---: |
| CNTT | 9 | 75 |
| KTPM | 7 | 78 |
| HTTT | 4 | 77,5 |

**KTPM có trung vị cao nhất, 78 điểm**. HTTT đứng tiếp theo với 77,5 điểm, sau đó là CNTT với 75 điểm. Kết luận mô tả bộ dữ liệu mẫu gồm 20 sinh viên; số lượng của ba nhóm khác nhau.

Trong boxplot, đường ngang bên trong hộp biểu diễn trung vị; hai cạnh hộp là Q1 và Q3. Theo mặc định, râu hộp kéo đến các điểm ngoài cùng còn nằm trong giới hạn 1,5 lần khoảng tứ phân vị; điểm vượt giới hạn được hiển thị riêng. Các nhãn trên ảnh là trung vị đã tính từ dữ liệu, không phải số gõ cố định.

## Kiến thức cần nắm

- **Figure** là toàn bộ khung hình; **Axes** là một vùng vẽ. Một Figure có thể chứa nhiều Axes. Báo cáo 1×2 có hai ô biểu đồ; ô phải có thêm Axes do dùng `twinx()` để biểu diễn đơn vị lượng mưa.
- Giao diện trạng thái `plt.plot(...)` vẽ lên Axes hiện hành. Giao diện hướng đối tượng `fig, ax = plt.subplots()` rồi `ax.plot(...)` chỉ rõ đối tượng cần thao tác; các bài dùng cách này để quản lý biểu đồ con.
- Line Plot dùng cho xu hướng theo tháng; Bar Chart so sánh ngân sách giữa các tháng; Scatter thể hiện quan hệ giữa hai biến số; Histogram/KDE xem phân bố; Boxplot so sánh phân bố giữa các nhóm. Heatmap phù hợp với ma trận nhưng không nằm trong các nhiệm vụ thực hành của đề này.
- `fig.savefig(..., dpi=300)` xuất ảnh. `layout="constrained"` bố trí khoảng trống cho tiêu đề, nhãn trục và chú thích; `plt.close(fig)` giải phóng Figure sau khi lưu.
- Backend `Agg` dùng để xuất ảnh tự động, không mở cửa sổ tương tác. Font DejaVu Sans hỗ trợ nhãn tiếng Việt.

## Kiểm thử

Chạy từ thư mục gốc dự án:

```powershell
.\Lab5\.venv\Scripts\python.exe -B -X utf8 Lab5\test_lab5.py
```

Bộ kiểm thử gồm **10 test**: dữ liệu kinh doanh; trung vị và số lượng từng ngành; trung vị với nhóm chẵn/lẻ chưa sắp xếp; từ chối list rỗng hoặc lệch độ dài; nội dung đường doanh số; cột quảng cáo và chú thích; dữ liệu/đơn vị/kích thước báo cáo; histogram có 6 khoảng và KDE; scatter đủ 20 điểm và 3 nhóm màu; boxplot với trung vị và số lượng đúng.

Kết quả chạy: **10/10 test đạt**. Cả hai chương trình đã chạy thành công từ thư mục gốc dự án. Đã kiểm tra trực quan đủ sáu ảnh: nhãn tiếng Việt và chú thích rõ, không bị cắt; kích thước ảnh đúng như bảng trên. Metadata PNG ghi xấp xỉ 299,9994 DPI do quy đổi sang pixel/mét, tương đương thiết lập 300 DPI.

Khi chạy kiểm thử, Seaborn 0.13.2 phát sinh `MatplotlibDeprecationWarning` về tham số `vert` khi vẽ boxplot với Matplotlib 3.11.2. Cảnh báo xuất phát từ lời gọi nội bộ của thư viện; biểu đồ và các kiểm thử vẫn tạo thành công. Các phiên bản trong `requirements.txt` giữ môi trường ở bộ phiên bản đã kiểm tra.

## Tài liệu tham khảo

- [Matplotlib Figure.savefig](https://matplotlib.org/stable/api/_as_gen/matplotlib.figure.Figure.savefig.html): xuất ảnh và thiết lập DPI.
- [Seaborn histplot](https://seaborn.pydata.org/generated/seaborn.histplot.html): histogram và KDE.
- [Seaborn boxplot](https://seaborn.pydata.org/generated/seaborn.boxplot.html): biểu diễn phân bố, trung vị và râu hộp.
