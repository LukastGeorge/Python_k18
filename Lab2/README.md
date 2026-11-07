# Lab 2 - Lập trình căn bản trong Python (Phần 2)

Bài làm theo `Lab2_PP_Basic_P2.pdf`. Sử dụng thư mục `Lab2` đã có sẵn thay cho tên `ch1-basic-p2` trong đề.

## Các file bài tập

| Mục trong đề | File | Nội dung |
| --- | --- | --- |
| 3.1 | `ex01_advanced_vars.py` | Chuỗi, gán đồng thời, xoay vòng ba biến, gán chuỗi, sai số số thực; minh họa thêm `+=` và `None`. |
| 3.2 | `ex02_advanced_control.py` | Truthy/Falsy, kiểm tra tên, PIN với `while...else`, phí vận chuyển dùng ternary; minh họa thêm `for...else`. |
| 3.3 | `ex03_functions_design.py` | Hàm lãi kép thuần, docstring, `help()`, tham số vị trí, mặc định và từ khóa. |
| 3.4 | `ex04_advanced_io.py` | Nhập số nguyên và tên hợp lệ, `sep`/`end`, thanh tiến trình, escape và raw string. |
| 3.5 | `ex05_advanced_exceptions.py` | `raise`, Call Stack/Traceback, đọc tệp với `try-except-else-finally`, LBYL và EAFP. |
| Dữ liệu mẫu | `payment_data.txt` | Chứa số `20`, dùng cho phép tính `100 / 20` trong bài 3.5. |

Mỗi file Python chạy độc lập. Chỉ sử dụng thư viện chuẩn, không cần cài thêm gói.

## Cách chạy bằng PowerShell

Dùng Python trong môi trường `venv` đã có, không cần kích hoạt môi trường:

```powershell
Set-Location 'E:\Workspace\Python_k18\Lab2'
.\venv\Scripts\python.exe -X utf8 ex01_advanced_vars.py
.\venv\Scripts\python.exe -X utf8 ex02_advanced_control.py
.\venv\Scripts\python.exe -X utf8 ex03_functions_design.py
.\venv\Scripts\python.exe -X utf8 ex04_advanced_io.py
.\venv\Scripts\python.exe -X utf8 ex05_advanced_exceptions.py
```

Chạy từng lệnh. Bài 3.2 và 3.4 sẽ dừng để chờ bạn nhập dữ liệu:

- **Bài 3.2:** nhập tên, sau đó nhập PIN `2026` để đăng nhập thành công. Chạy lại và nhập sai ba lần để quan sát khối `else`. Nhập đúng ngay lần thứ ba vẫn đăng nhập được và không in thông báo khóa.
- **Bài 3.4:** nhập họ tên chỉ gồm chữ cái và dấu cách, sau đó nhập số nguyên từ `-10` đến `100`. Có thể thử tên `An123`, số `abc`, `2.5` hoặc `101` để thấy chương trình yêu cầu nhập lại. Thanh tiến trình mất khoảng 3,3 giây.
- **Bài 3.5:** Traceback chia cho 0 là lỗi được tạo có chủ đích để học cách đọc vết lỗi. Lỗi được bắt nên các ví dụ sau vẫn chạy. Tệp mẫu được tìm theo vị trí file Python.

## Phần 2 - REPL, SyntaxError và tra cứu module

Mở REPL từ thư mục `Lab2`:

```powershell
.\venv\Scripts\python.exe -X utf8
```

Tại dấu nhắc `>>>`, nhập từng biểu thức (không gõ lại ký hiệu `>>>`):

```pycon
>>> 2 + 3 * 4 ** 2
50
>>> 'Python ' * 3 + '3.12'
'Python Python Python 3.12'
>>> 10 / 2
5.0
>>> 10 // 2
5
```

REPL lặp bốn bước: đọc câu lệnh (Read), đánh giá biểu thức (Eval), hiển thị giá trị (Print), chờ câu lệnh tiếp theo (Loop). Trong biểu thức đầu, lũy thừa được tính trước phép nhân, rồi mới cộng. `/` trả về số thực; `//` chia lấy phần nguyên theo hướng làm tròn xuống. Phép gán như `total_score = 100` không tự in giá trị trong REPL.

### Nhận diện và sửa lỗi cú pháp

| Lệnh gây lỗi | Nguyên nhân | Một cách sửa hợp lệ |
| --- | --- | --- |
| `42 + 5 + * 2` | Toán tử `*` không có toán hạng bên trái hợp lệ sau `+`. | `42 + 5 * 2` cho kết quả `52`. |
| `'Chao mung ban"` | Dấu nháy mở và đóng không cùng loại. | `'Chao mung ban'` |
| `100 = total_score` | Không thể gán giá trị cho hằng số `100`. | `total_score = 100` |

Ví dụ vết lỗi của lệnh đầu trên Python 3.12:

```text
  File "<console>", line 1
    42 + 5 + * 2
             ^
SyntaxError: invalid syntax
```

Con trỏ `^` chỉ vị trí Python phát hiện vấn đề; nguyên nhân cũng có thể nằm phía trước vị trí đó. `SyntaxError` xảy ra khi phân tích cú pháp, trước khi câu lệnh được thực thi. Các lệnh sai được đặt trong tài liệu này để các file bài tập vẫn chạy được.

### Khám phá module

```pycon
>>> import math
>>> dir(math)
>>> help(math.isclose)
>>> math.isclose(0.1 + 0.2, 0.3)
True
>>> exit()
```

`dir(math)` liệt kê các tên của module, chẳng hạn `pi`, `sqrt`, `isclose`. `help(math.isclose)` hiển thị mô tả cùng chữ ký `isclose(a, b, *, rel_tol=1e-09, abs_tol=0.0)`. `rel_tol` là sai số tương đối và `abs_tol` là sai số tuyệt đối, hữu ích khi so sánh gần số 0. Dùng `import math` giúp thể hiện nguồn gốc hàm và tránh xung đột tên do `from math import *`.

## Ghi chú kết quả

- `0.1 + 0.2` cho `0.30000000000000004`; so sánh trực tiếp với `0.3` cho `False`, còn so sánh epsilon và `math.isclose()` đều cho `True` trong ví dụ này.
- Sau `a, b, c = b, c, a`, bộ `(1, 2, 3)` trở thành `(2, 3, 1)`.
- `0.0`, `''`, `None`, `[]`, `{}` là Falsy; `' '` và `[0]` là Truthy.
- Đơn hàng `499999` đồng có phí `30000` đồng; từ `500000` đồng trở lên có phí `0` đồng.
- Hàm lãi kép trả **tổng tiền gốc và lãi** theo công thức đề bài. Muốn lấy riêng tiền lãi, trừ đi `principal`. Hàm không nhập/xuất dữ liệu hoặc sửa trạng thái bên ngoài.
- Ví dụ gửi `100000000` đồng, lãi suất `0.07`, thời gian `5` năm: nhập lãi hàng tháng được khoảng `141.762.525,96` đồng; nhập lãi hàng năm được khoảng `140.255.173,07` đồng.
- Khối `else` của vòng lặp chạy khi vòng lặp kết thúc tự nhiên, và bị bỏ qua khi gặp `break`. Khối `else` của `try` chỉ chạy khi phần `try` không phát sinh ngoại lệ. Khối `finally` luôn chạy khi rời cấu trúc xử lý ngoại lệ.
- Đọc Traceback từ dưới lên: xem loại lỗi và thông điệp ở cuối, rồi xem dòng gây lỗi trong `data_layer()`, tiếp đến `service_layer()` và `main()`.
- LBYL kiểm tra điều kiện trước khi thao tác. EAFP thực hiện trong `try` rồi bắt các ngoại lệ dự kiến. Bài 3.5 dùng cùng dữ liệu hợp lệ, thiếu khóa và sai định dạng để so sánh hai cách.

## Kiểm tra đã thực hiện

Đã chạy cả năm chương trình bằng Python 3.12.10 trong `Lab2/venv`, bao gồm chạy từ thư mục cha để kiểm tra đường dẫn tệp dữ liệu. Đã kiểm tra các trường hợp sau:

- So sánh epsilon tại biên; đúng/sai của các giá trị Truthy/Falsy; tìm kiếm có và không có kết quả.
- PIN đúng lần đầu, đúng lần thứ ba, sai cả ba lần; phí vận chuyển ngay dưới và tại ngưỡng `500000`.
- Lãi kép theo giá trị biết trước, lãi suất bằng 0, thời gian bằng 0; đối chiếu kết quả hàng tháng với phép cộng lãi từng kỳ bằng `decimal.Decimal`.
- Nhập sai định dạng, ngoài khoảng, hai đầu mút hợp lệ; tên rỗng, có số/ký tự đặc biệt và tên tiếng Việt hợp lệ.
- Thanh toán hợp lệ, hết số dư, số tiền không dương và vượt số dư; đọc tệp thành công, thiếu tệp, nội dung sai và chia cho 0.
- LBYL và EAFP cho cùng kết quả với các bộ dữ liệu mẫu; Traceback minh họa không ngăn các ví dụ còn lại chạy tiếp.
