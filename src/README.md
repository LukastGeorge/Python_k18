# Môi trường chạy Lab01–Lab05

Các notebook dùng **Python 3.11**, **TensorFlow 2.15.1 / Keras 2.15** và
**NumPy 1.26.4**. Mã kiểm tra Lab05 sử dụng API Keras 2, vì vậy không nâng
TensorFlow/Keras lên phiên bản mới tùy ý.

IPython được ghim ở **8.37.0** để lệnh `%matplotlib widget` hoạt động với
Matplotlib 3.8.4 khi khởi động kernel mới.

Môi trường dành cho các bài trong `src` nằm tại `.venv-src` ở thư mục gốc
`Python_k18`.

## Chạy trong VS Code

1. Mở thư mục `E:\Workspace\Python_k18`.
2. Chạy **Python: Select Interpreter** từ Command Palette, chọn
   `.venv-src\Scripts\python.exe`.
3. Mở notebook `.ipynb`, bấm **Select Kernel** và chọn
   **Python 3.11 (Python_k18 - src)**.
4. Chạy các ô từ trên xuống. Các file `*_utils.py` và `autils.py` là thư viện
   hỗ trợ; nội dung bài học và các bước thực hành nằm trong notebook.

Lab05 đã được điền hai vùng `START CODE HERE`: hàm Softmax bằng NumPy và
mạng Dense `400 → 25 (ReLU) → 15 (ReLU) → 10 (Linear)`. Chạy từ trên xuống
để kiểm tra bài làm, huấn luyện 40 epoch và xem kết quả dự đoán.

Notebook đã lưu kết quả chạy đủ **22 ô code**. Cả hai bộ kiểm tra có sẵn
đều đạt. Sau 40 epoch, loss cuối là **0.0357**, dự đoán sai **43/5.000 ảnh**,
tương ứng độ chính xác **99,14% trên tập huấn luyện**. Đây là kết quả trên
dữ liệu dùng để huấn luyện, chưa phải đánh giá trên tập kiểm tra độc lập.
Hàm Softmax cũng đã được kiểm tra với đầu vào có giá trị lớn để xác nhận
không bị tràn số. Kết quả có thể thay đổi nhẹ khi huấn luyện lại.

## Terminal PowerShell

Mở terminal mới trong VS Code để nhận cấu hình môi trường. Có thể gọi trực
tiếp Python của môi trường từ thư mục gốc mà không cần kích hoạt:

```powershell
& .\.venv-src\Scripts\python.exe --version
& .\.venv-src\Scripts\python.exe -m pip check
```

Các bài dùng đường dẫn tương đối như `./deeplearning.mplstyle` và `data/X.npy`.
Khi chạy mã bằng terminal, chuyển vào thư mục chứa notebook tương ứng trước.
VS Code đã được cấu hình dùng thư mục notebook khi chạy notebook.

## Cài lại thư viện nếu cần

Chạy từ thư mục gốc với môi trường Python 3.11 đã tạo:

```powershell
& .\.venv-src\Scripts\python.exe -m pip install -r .\src\requirements.txt
& .\.venv-src\Scripts\python.exe -m pip install torch==2.14.1+cpu --index-url https://download.pytorch.org/whl/cpu
& .\.venv-src\Scripts\python.exe -m ipykernel install --user --name python-k18-src --display-name "Python 3.11 (Python_k18 - src)"
```

PyTorch dùng bản CPU để chạy Lab04 trên Windows.
