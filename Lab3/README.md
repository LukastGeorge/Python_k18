# Lab 3 - Kiểu dữ liệu phức tạp trong Python

Bài làm theo `Lab3_PP_Collection_types.docx`, gồm đủ các nhiệm vụ từ bài 3.1 đến 3.5. Các file được đặt trong thư mục `Lab3` theo yêu cầu, thay cho tên `ch2-collections` trong đề.

## Môi trường

Lab3 có môi trường ảo riêng tại `.venv`, dùng cùng Python và phiên bản thư viện với `Lab1/.venv`:

| Thành phần | Phiên bản |
| --- | --- |
| Python | 3.14.4 |
| pip | 26.2.1 |
| NumPy | 2.5.2 |
| pandas | 3.0.5 |
| python-dateutil | 2.9.0.post0 |
| six | 1.17.0 |
| tzdata | 2026.3 |

Các bài Lab3 chỉ cần thư viện chuẩn; các gói trên được cài để đồng bộ môi trường với Lab1. Danh sách phiên bản thư viện nằm trong `requirements.txt`.

## Chạy từng bài bằng PowerShell

Không cần kích hoạt môi trường; gọi trực tiếp Python trong `.venv`:

```powershell
Set-Location 'E:\Workspace\Python_k18\Lab3'
.\.venv\Scripts\python.exe -X utf8 ex01_list_operations.py
.\.venv\Scripts\python.exe -X utf8 ex02_tuple_unpacking.py
.\.venv\Scripts\python.exe -X utf8 ex03_set_operations.py
.\.venv\Scripts\python.exe -X utf8 ex04_dict_mastery.py
.\.venv\Scripts\python.exe -X utf8 ex05_nested_structures.py
```

Cả năm bài chạy độc lập bằng dữ liệu mẫu có sẵn, không yêu cầu nhập từ bàn phím. Những thông báo `IndexError`, `ValueError`, `TypeError` và `KeyError` được in trong ví dụ là minh họa có chủ đích; lỗi đã được bắt để chương trình tiếp tục chạy.

Nếu dùng VS Code, chọn **Python: Select Interpreter** rồi chọn `E:\Workspace\Python_k18\Lab3\.venv\Scripts\python.exe`.

## Nội dung và kết quả đối chiếu

| Bài | File | Nội dung |
| --- | --- | --- |
| 3.1 | `ex01_list_operations.py` | List CRUD, slicing, sort/sorted, aliasing và id, ma trận 2D, shallow/deep copy, list comprehension. |
| 3.2 | `ex02_tuple_unpacking.py` | Tuple một phần tử, tính bất biến, cập nhật qua list, extended unpacking, xoay vòng biến, trả tuple và nhận `*args`. |
| 3.3 | `ex03_set_operations.py` | Lọc trùng, add/update/remove/discard, đại số tập hợp, quan hệ tập hợp, set comprehension và frozenset làm khóa. |
| 3.4 | `ex04_dict_mastery.py` | Kho linh kiện, get/in/keys/values/items, báo cáo giá trị kho, setdefault, gom nhóm và dict comprehension. |
| 3.5 | `ex05_nested_structures.py` | Giỏ hàng của ba khách, tính hóa đơn VIP, thêm sản phẩm, tìm khách chi nhiều nhất và pprint. |

### Bài 3.1 - List

- Sau CRUD: `[7.5, 8.0, 8.75, 9.0, 8.5, 7.0, 9.5]`; `last_score = 10.0`.
- Ba điểm đầu: `[7.5, 8.0, 8.75]`; ba điểm cuối: `[8.5, 7.0, 9.5]`.
- `sort(reverse=True)` sửa trực tiếp `scores`; `sorted(scores)` tạo list tăng dần mới và giữ nguyên `scores`.
- Sửa `alias_list[0]` làm `original_list[0]` thành `99`; hai biến có cùng `id()`.
- `grid_wrong` có ba chữ `X`, còn `grid_correct` chỉ có một chữ `X`.
- Sau khi sửa dữ liệu gốc: bản sao nông chứa `999`, bản sao sâu vẫn chứa `1`.
- Điểm đạt: `[7.0, 8.5, 9.5, 6.0, 5.5, 10.0]`; điểm cộng ưu tiên không vượt quá `10.0`.

### Bài 3.2 - Tuple

- `("GDU")` là `str`, còn `("GDU",)` là `tuple`.
- `exam_scores = [8.5, 9.0, 7.5, 8.0]`; điểm trung bình `8.25`.
- Xoay vòng ba biến cho `a = 200`, `b = 300`, `c = 100`.
- `analyze_numbers([12, 45, 67, 23, 89, 34])` trả `(12, 89, 45.0)`; danh sách rỗng gây `ValueError` có thông báo rõ ràng.
- Chu vi tam giác `(3, 4, 5)` là `12`; tứ giác `(2, 3, 4, 5)` là `14`; ngũ giác `(2, 3, 4, 5, 6)` là `20`.
- Dưới ba cạnh hoặc có cạnh không dương gây `ValueError` đúng thông báo trong đề. Hàm kiểm tra hai điều kiện này theo phạm vi bài tập.

### Bài 3.3 - Set

- ID đã lọc trùng và sắp xếp: `[101, 102, 105, 108, 109, 110]`.
- Hợp AI/Web có 9 người; giao có `Binh`, `Dung`, `Khoa`; chỉ thuộc AI có `An`, `Chi`, `Hoa`.
- Hiệu đối xứng có `An`, `Chi`, `Hanh`, `Hoa`, `Lan`, `Mai`; giao cả ba CLB có `Dung`, `Khoa`.
- Tập ký tự có mã ASCII chẵn gồm 8 chữ: `d`, `h`, `l`, `n`, `p`, `r`, `t`, `v`.
- `security_matrix[admin_roles]` trả `Toàn quyền Quản trị (SuperAdmin)`.
- Set không có thứ tự; vị trí phần tử khi in trực tiếp có thể khác giữa các lần chạy. Các kết quả CLB được in qua `sorted()` để dễ đối chiếu.

### Bài 3.4 - Dictionary

- `inventory.get("monitor", 0)` trả `0`; `cpu` có trong kho, `case` chưa có.
- Tổng giá trị kho: **277.500.000 VNĐ**; `gpu` có giá trị tồn kho lớn nhất: **68.000.000 VNĐ**.
- Từ khóa `python` và `ai` xuất hiện 3 lần; `django`, `fastapi`, `docker`, `pandas` xuất hiện 1 lần.
- Gom nhóm: `KTPM` gồm Tran An và Hoang Chi; `CNTT` gồm Le Binh và Nguyen Hoa; `ATTT` gồm Pham Dung và Do Khoa.
- Điểm thang 4: `{'An': 3.4, 'Binh': 2.4, 'Chi': 3.8, 'Dung': 1.8, 'Hoa': 3.0, 'Khoa': 1.4}`.
- Sinh viên từ 8 điểm: `{'An': 8.5, 'Chi': 9.5}`.

### Bài 3.5 - Cấu trúc lồng nhau

- CUST01 ban đầu mua một bàn phím và hai chuột: tiền gốc **2.150.000 đồng**, sau giảm VIP 10% còn **1.935.000 đồng**.
- Thêm SP02 một lần làm số lượng tăng từ 2 lên 3 và không thêm dòng sản phẩm trùng.
- Thêm SP03 tạo một phần tử mới; CUST01 có tiền gốc **4.400.000 đồng**, thực trả **3.960.000 đồng**.
- Với bộ dữ liệu mẫu, khách chi nhiều nhất là **CUST02 - Trần Thị Bình**, thực trả **4.000.000 đồng**. CUST03 có tiền gốc 4.200.000 đồng nhưng chỉ trả 3.780.000 đồng sau giảm VIP, nên không đứng đầu.
- Khách không tồn tại: tính hóa đơn trả `(0, 0)`; thêm sản phẩm gây `KeyError`. `find_top_spender({})` trả `None`; nếu đồng hạng thì chọn khách được chèn trước.
- Sản phẩm mới được thêm trực tiếp vào giỏ đúng yêu cầu đề, nên giỏ và biến `new_product` cùng tham chiếu dict đó.
- Cuối bài có cả `print()` và `pprint.pprint(ecommerce_system, indent=4, width=70)` để so sánh định dạng.

## Ghi nhớ khi chọn cấu trúc dữ liệu

List phù hợp với dãy dữ liệu cần thêm/sửa/xóa; tuple phù hợp với bản ghi cố định; set phù hợp với lọc trùng và kiểm tra thành viên; dict phù hợp với tra cứu theo khóa và biểu diễn đối tượng. Set và dict thường tra cứu thành viên nhanh hơn việc duyệt lần lượt list khi dữ liệu lớn.

Khóa dict và phần tử set phải **hashable**. Tuple là bất biến nhưng chỉ hashable khi tất cả phần tử bên trong cũng hashable; tuple chứa list không dùng làm khóa dict được. `frozenset` giữ tập phần tử bất biến và có thể làm khóa. Tính bất biến của tuple cũng không ngăn một list nằm bên trong tuple bị sửa.

Phép gán `b = a` không sao chép đối tượng. Shallow copy tạo lớp ngoài mới nhưng còn dùng chung các phần tử con; deep copy sao chép các cấu trúc con. Dùng comprehension để tạo các dòng ma trận độc lập.

## Kiểm tra bài làm

Đã chạy trực tiếp cả năm file bằng Python trong `Lab3/.venv`: tất cả kết thúc thành công và không có lỗi chưa được xử lý. Đã kiểm tra 11 nhóm tình huống, gồm kết quả list/slicing/copy/comprehension, tuple và chu vi không hợp lệ, phép toán set, tổng kho, thống kê/gom nhóm, hóa đơn VIP, thêm hàng trùng/mới, khách không tồn tại và chọn khách theo số tiền sau giảm giá. Cả 11 nhóm kiểm tra đều đạt.

Đã đối chiếu toàn bộ tên và phiên bản gói bằng `pip list`: Lab3 khớp hoàn toàn với Lab1. Import và phép tính thử với NumPy/pandas đều thành công; `pip check` báo không có xung đột thư viện.
