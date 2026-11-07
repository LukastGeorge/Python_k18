# ex06_exception.py
# Xử lý ngoại lệ (Exception Handling)
def divide_numbers():
    print("--- Xử lý ngoại lệ an toàn ---")
    try:
        a = float(input("Nhập số bị chia (a): "))
        b = float(input("Nhập số chia (b): "))
        result = a / b
    except ZeroDivisionError:
        print("Lỗi: Không thể thực hiện phép chia cho số 0!")
    except ValueError:
        print("Lỗi: Dữ liệu nhập vào phải là số thực hợp lệ!")
    else:
        print(f"Kết quả phép chia: {a} / {b} = {result:.4f}")
    finally:
        print("Khối finally: Hoàn tất quá trình tính toán.")
if __name__ == "__main__":
 divide_numbers()