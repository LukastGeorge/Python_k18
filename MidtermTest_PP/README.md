# Bài kiểm tra giữa kỳ Lập trình Python

- Sinh viên: **Nguyễn Duy Trường**.
- MSSV: **24150180**.
- Lớp học phần: **020100138002**.
- Ngày kiểm tra: **10/10/2026**.
- Đề: `261010_LT-Python_De-kiem-tra.docx`.

## Cấu trúc

```text
MidtermTest_PP/
├── src/
│   ├── __init__.py
│   ├── quan_ly_trung_tam.py
│   ├── main.py
│   └── phan_tich_bo_nho.py
├── docs/
│   ├── MidtermTest_PP_24150180.docx
│   ├── MidtermTest_PP_24150180.pdf
│   └── phan_tich_va_thiet_ke.md
├── tests/
│   └── test_quan_ly_trung_tam.py
└── README.md
```

Báo cáo có bản Word có thể chỉnh sửa và bản PDF, trả lời phần I, II và giải thích phần III; bản Markdown cùng nội dung được giữ làm nguồn. Mã nguồn chỉ dùng thư viện chuẩn Python, không cần cài gói hoặc tạo môi trường ảo mới.

## Chạy bằng PowerShell

```powershell
Set-Location 'E:\Workspace\Python_k18\MidtermTest_PP'
python -B -X utf8 src\phan_tich_bo_nho.py
python -B -X utf8 src\main.py
python -B -X utf8 -m unittest discover -s tests -v
```

Khi giải nén ở máy khác, chuyển tới thư mục `MidtermTest_PP` vừa giải nén rồi chạy ba lệnh Python tương tự. `-X utf8` hỗ trợ in tiếng Việt; `-B` tránh tạo bytecode. Đã xác minh bằng Python 3.14.4.

## Kết quả chính

Năm dòng câu 1.1:

```text
1. list_a[0] = 99
2. list_a[1] = [20, 30, 40]
3. list_a[2] = {'a': 1, 'b': 2}
4. list_b is list_a: True
5. list_c is list_a: False
```

- Hai lần đăng ký `Python Basic` chỉ có một khóa; tổng học phí **1500000**.
- Thêm `IELTS Foundation` học phí 2000000 thì tổng là **3500000**.
- Học phí 0/âm gây `ValueError("Học phí phải lớn hơn 0!")`.
- `tim_hoc_vien("HV99")` trả về `None`; không phát sinh `KeyError`.
- Hai học viên cùng `ma_id` được coi là bằng nhau qua `__eq__`, dù họ tên/email khác nhau.
- Mỗi học viên có set khóa học riêng; mỗi trung tâm có dictionary riêng.
- **17/17 kiểm thử đạt**, bao gồm dữ liệu sai và tính toàn vẹn trạng thái.

## Quy tắc triển khai

`Nguoi` là lớp cha của `HocVien` và `GiangVien`. Hai lớp con dùng `super().__init__()`; phần hiển thị mở rộng dùng `super().hien_thi_thong_tin()`. `__str__` giữ đúng dạng `[MA_ID] Ho Ten`.

`__tong_hoc_phi` và `__luong_theo_gio` là thuộc tính private. Property cung cấp getter/setter, chỉ chấp nhận số hữu hạn không âm. Riêng học phí khi đăng ký khóa phải lớn hơn 0. Setter tổng tiền cho phép điều chỉnh tổng theo ràng buộc này; mô hình không có sổ giao dịch hoặc phân quyền tài chính.

Tên khóa được loại khoảng trắng hai đầu, so sánh phân biệt hoa/thường. Chương trình kiểm tra khóa tồn tại trước khi cộng tiền để không thu học phí hai lần. Set không bảo đảm thứ tự in; demo nhiều khóa dùng `sorted()` để dễ đọc.

`QuanLyTrungTam.them_hoc_vien()` từ chối mã đã tồn tại, giữ nguyên học viên cũ. Tra cứu dùng `dict.get()` đúng yêu cầu đề. Hệ thống là chương trình minh họa trong bộ nhớ; chưa bổ sung lưu file, cơ sở dữ liệu hoặc giao diện vì đề không yêu cầu.

## Gói nộp bài

File ZIP được đặt ở thư mục cha, tên:

```text
MidtermTest_PP_24150180_NguyenDuyTruong.zip
```

ZIP chứa thư mục gốc `MidtermTest_PP` với mã nguồn, báo cáo, kiểm thử và README. Không chứa môi trường ảo, bytecode hoặc ảnh kiểm tra bố cục. Bài được chuẩn bị tại máy, chưa tải lên Google Classroom.
