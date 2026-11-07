# Lab 4 - Lập trình hướng đối tượng trong Python

Bài làm theo `Lab4_PP_OOP.docx`, gồm bốn bài từ mục 3.1 đến 3.4. Mã nguồn nằm trong `Lab4` để thống nhất với các lab trước, thay cho tên `ch3-oop` trong đề. Mỗi bài có lớp, phương thức, chú thích và hàm `main()` minh họa bằng dữ liệu của đề.

## Các file bài tập

| Mục trong đề | File | Nội dung |
| --- | --- | --- |
| 3.1 | `ex01_country_class.py` | Lớp Country, constructor, self, validation, mật độ dân số, so sánh diện tích, `__str__` và `__repr__`. |
| 3.2 | `ex02_continent_composition.py` | Continent chứa các Country, biến lớp đếm đối tượng, thống kê tổng, quốc gia lớn nhất và `__len__`. |
| 3.3 | `ex03_encapsulation_nematode.py` | Thuộc tính private, getter/setter, kiểm tra dữ liệu, sinh trưởng và name mangling. |
| 3.4 | `ex04_academic_inheritance.py` | Member, Student, Faculty; `super()`, ghi đè phương thức, đa hình, quản lý môn học và MRO. |
| Kiểm thử | `test_lab4.py` | 22 bài kiểm thử tự động bằng `unittest`, bao gồm nhiều bộ dữ liệu sai và trường hợp biên. |

## Cách chạy bằng PowerShell

Các bài chỉ dùng thư viện chuẩn, không cần cài thêm gói. Có thể dùng ngay Python trong môi trường Lab3 đã có:

```powershell
Set-Location 'E:\Workspace\Python_k18'
.\Lab3\.venv\Scripts\python.exe -X utf8 Lab4\ex01_country_class.py
.\Lab3\.venv\Scripts\python.exe -X utf8 Lab4\ex02_continent_composition.py
.\Lab3\.venv\Scripts\python.exe -X utf8 Lab4\ex03_encapsulation_nematode.py
.\Lab3\.venv\Scripts\python.exe -X utf8 Lab4\ex04_academic_inheritance.py
```

Chạy từng lệnh. Cả bốn bài đều sử dụng dữ liệu mẫu, không yêu cầu nhập từ bàn phím. Các thông báo lỗi trong ví dụ là tình huống được tạo và bắt có chủ đích để chương trình tiếp tục chạy.

Nếu đã cấu hình lệnh `python`, có thể thay `.\Lab3\.venv\Scripts\python.exe` bằng `python`. Bài Lab4 không phụ thuộc các gói đã cài trong Lab3. Giữ bốn file bài tập cùng thư mục vì bài 3.2 import lớp Country từ bài 3.1. Khối `if __name__ == "__main__":` ngăn phần minh họa của bài 3.1 chạy khi được import.

Chạy bộ kiểm thử:

```powershell
.\Lab3\.venv\Scripts\python.exe -B -X utf8 Lab4\test_lab4.py
```

Tùy chọn `-X utf8` giúp hiển thị tiếng Việt; `-B` tránh tạo file bytecode trong lần kiểm thử.

## Kết quả đối chiếu

### Bài 3.1 - Country

- Canada có mật độ `3.4535722262227995` người/km²; Vietnam có mật độ khoảng `295.883` người/km².
- `canada.is_larger(usa)` trả về `True`; `vietnam.is_larger(canada)` trả về `False`.
- `str(canada)` là `Canada has a population of 34482779 and is 9984670 square km.`
- `repr(canada)` là `Country('Canada', 34482779, 9984670)`.
- `print(countries)` dùng `repr()` cho từng phần tử, giúp nhận biết lớp và dữ liệu của mỗi đối tượng; `print(canada)` dùng `str()` để hiển thị thân thiện.
- Dân số bằng 0 hợp lệ theo điều kiện `population < 0` của nhiệm vụ 1. Dân số âm, diện tích không dương và so sánh với đối tượng sai kiểu đều bị từ chối.

`Country` là bản thiết kế; Canada, USA và Vietnam là các đối tượng được tạo từ lớp đó. `self` tham chiếu đối tượng đang nhận lời gọi: `canada.population_density()` tương đương `Country.population_density(canada)`. Các thuộc tính được gán qua `self` thuộc riêng từng đối tượng.

### Bài 3.2 - Continent

- North America chứa Canada, USA và Mexico: tổng dân số `460733357`, tổng diện tích `21755295` km², quốc gia lớn nhất là Canada.
- Asia được khởi tạo rỗng rồi thêm Vietnam; `len(asia) == 1`.
- Chạy file một lần trong tiến trình mới cho `Continent.total_continents == 2`.
- Châu lục rỗng có tổng dân số, tổng diện tích và số quốc gia bằng 0; `get_largest_country()` trả về `None`.
- `str(continent)` hiển thị tên châu lục ở dòng đầu, sau đó mỗi quốc gia trên một dòng.

Biến lớp `total_continents` đếm số đối tượng đã khởi tạo thành công trong tiến trình, không phải số đối tượng còn tồn tại. Danh sách `countries` thuộc riêng từng châu lục. Constructor sao chép danh sách đầu vào nhưng giữ tham chiếu tới các đối tượng Country bên trong. Đây là quan hệ chứa đựng (*has-a*): châu lục có các quốc gia.

### Bài 3.3 - Nematode

- Với `Nematode(1.05, 'hermaphrodite', 3)`, gọi `grow(2, 0.15)` cho tuổi 5 ngày và chiều dài 1.2 mm.
- Sau tăng trưởng: `Nematode(Length: 1.2mm, Gender: hermaphrodite, Age: 5 days)`.
- Truy cập trực tiếp `n1.__body_length` bên ngoài lớp gây `AttributeError`; `n1._Nematode__body_length` đọc được giá trị.
- Giới tính được chuyển về chữ thường; `'MALE'` trở thành `'male'`, còn `'female'` bị từ chối.
- Setter tuổi cho phép giữ nguyên hoặc tăng tuổi; không cho phép giảm tuổi, tuổi âm hay tuổi không nguyên.
- `grow()` yêu cầu số ngày nguyên không âm và mức tăng chiều dài không âm. Nếu dữ liệu sai hoặc chiều dài kết quả không hợp lệ, cả tuổi và chiều dài đều giữ nguyên.

Tiền tố `_` là quy ước thuộc nội bộ. Tiền tố `__` kích hoạt name mangling, đổi tên thuộc tính để hạn chế truy cập nhầm và xung đột tên trong kế thừa; nó không phải cơ chế bảo mật tuyệt đối. Getter/setter cung cấp nơi kiểm tra dữ liệu trước khi cập nhật.

### Bài 3.4 - Member, Student và Faculty

- Student và Faculty gọi `super().__init__()` để khởi tạo mã, tên và email, sau đó bổ sung thuộc tính riêng.
- Sinh viên mẫu đăng ký `Lập trình Python` và `Cơ sở dữ liệu`. Hoàn thành môn Python sẽ chuyển môn đó từ `current_courses` sang `courses_taken`.
- Giảng viên được phân công môn `Lập trình Python`; mỗi sinh viên và giảng viên có danh sách môn riêng.
- `get_role()` lần lượt trả về `Sinh viên Đại học`, `Giảng viên Khoa` và `Thành viên chung`.
- Một vòng lặp gọi cùng `get_role()` và `get_details()` trên danh sách hỗn hợp; mỗi đối tượng tự chọn phương thức phù hợp mà không cần kiểm tra kiểu bằng `if/else`.
- `isinstance(student, Member)`, `issubclass(Student, Member)` và `issubclass(Faculty, Member)` đều là `True`.
- MRO của Student là `['Student', 'Member', 'object']`: khi tìm phương thức, Python đi theo thứ tự này.

Kế thừa thể hiện quan hệ *is-a*: Student là một Member. `get_details()` ở lớp con gọi phiên bản lớp cha qua `super()` rồi nối thêm thông tin. `Member.__str__()` gọi `self.get_details()`, nên khi in Student hoặc Faculty vẫn nhận được thông tin mở rộng của lớp con.

## Một số lỗi cần nhận biết

| Lỗi | Ví dụ và nguyên nhân |
| --- | --- |
| `AttributeError` | Truy cập tên private chưa qua name mangling hoặc gọi thuộc tính chưa tồn tại. |
| `TypeError` | So sánh Country với chuỗi, thêm chuỗi vào Continent hoặc gọi hàm với sai số đối số. |
| `ValueError` | Giá trị đúng dạng nhưng không hợp lệ, như dân số âm, diện tích 0, giới tính ngoài hai giá trị cho phép hoặc giảm tuổi. Theo yêu cầu bài Nematode, tuổi không nguyên cũng gây lỗi này. |
| Quên `self` | Python tự truyền đối tượng khi gọi instance method; nếu thiếu tham số nhận đối tượng, lời gọi thường gây `TypeError`. |

`__repr__` của các lớp mô tả thông tin khởi tạo để gỡ lỗi. Với Student và Faculty, danh sách môn được cập nhật sau khi khởi tạo không nằm trong chuỗi `repr`; đây không phải cơ chế lưu và khôi phục toàn bộ trạng thái.

## Kiểm tra đã thực hiện

Đã chạy cả bốn file từ thư mục gốc dự án bằng Python 3.14.4 trong `Lab3/.venv`; tất cả kết thúc thành công. Bộ `unittest` đạt **22/22**, bao gồm:

- Giá trị mẫu, định dạng chuỗi, mật độ và so sánh diện tích của Country.
- Tổng dân số/diện tích, châu lục rỗng, bộ đếm, sai kiểu và danh sách độc lập của Continent.
- Getter/setter, name mangling, sinh trưởng, chuẩn hóa giới tính và trạng thái giữ nguyên khi cập nhật thất bại của Nematode.
- Khởi tạo kế thừa, chuyển môn, danh sách độc lập, vai trò, thông tin đa hình, `__repr__` và MRO của hệ thống học thuật.
