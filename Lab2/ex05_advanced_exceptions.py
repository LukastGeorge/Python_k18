"""Bài 5: Chủ động phát sinh lỗi, đọc traceback và xử lý ngoại lệ."""

from pathlib import Path
import sys
import traceback


def process_payment(account_id, amount, balance):
    """Kiểm tra giao dịch và trả về số dư còn lại nếu thanh toán thành công."""
    if amount <= 0:
        raise ValueError("Số tiền giao dịch phải lớn hơn 0!")
    if amount > balance:
        raise PermissionError("Số dư tài khoản không đủ để thực hiện giao dịch!")

    remaining_balance = balance - amount
    print(f"Tài khoản {account_id}: thanh toán thành công {amount:,} đồng.")
    return remaining_balance


def data_layer():
    """Cố ý gây lỗi chia cho 0 ở tầng xử lý dữ liệu."""
    return 100 / 0


def service_layer():
    """Gọi tầng dữ liệu; ngoại lệ sẽ truyền về nơi gọi hàm này."""
    return data_layer()


def process_data_file(file_path):
    """Đọc một số trong tệp và tính 100 / số đó, trả None nếu gặp lỗi."""
    try:
        # with tự động đóng tệp, kể cả khi đọc hoặc chuyển kiểu bị lỗi.
        with open(file_path, "r", encoding="utf-8") as data_file:
            value = float(data_file.read().strip())
            result = 100 / value
    except FileNotFoundError as err:
        print(f"Không tìm thấy tệp: {err}")
        return None
    except ValueError as err:
        print(f"Nội dung tệp không phải là số hợp lệ: {err}")
        return None
    except ZeroDivisionError as err:
        print(f"Không thể chia cho 0: {err}")
        return None
    else:
        # else chỉ chạy khi toàn bộ khối try không phát sinh ngoại lệ.
        print(f"Đọc và tính toán thành công: 100 / {value:g} = {result:g}")
        return result
    finally:
        # finally luôn chạy, kể cả khi các nhánh phía trên dùng return.
        print("Đã kết thúc quá trình xử lý tệp.")


def get_age_lbyl(data):
    """LBYL: kiểm tra trước; tuổi là chuỗi chữ số thập phân không âm."""
    # Cho phép khoảng trắng ở hai đầu, ví dụ " 20 ".
    if "age" in data:
        text = data["age"]
        if isinstance(text, str):
            text = text.strip()
            if text.isdecimal():
                age = int(text)
                print(f"LBYL: tuổi hợp lệ là {age}.")
                return age
            else:
                print("LBYL: tuổi phải là chuỗi chữ số thập phân không âm.")
        else:
            print("LBYL: giá trị tuổi phải là chuỗi.")
    else:
        print("LBYL: không có khóa 'age'.")
    return None


def get_age_eafp(data):
    """EAFP: thử truy cập/chuyển kiểu rồi bắt lỗi nếu dữ liệu không hợp lệ."""
    try:
        text = data["age"]
        age = int(text)
        # Áp dụng cùng quy tắc chuỗi chữ số như phiên bản LBYL.
        if not isinstance(text, str):
            raise TypeError("Giá trị tuổi phải là chuỗi.")
        if not text.strip().isdecimal():
            raise ValueError("Tuổi phải là chuỗi chữ số thập phân không âm.")
    except KeyError as err:
        print(f"EAFP: không có khóa {err}.")
        return None
    except TypeError as err:
        print(f"EAFP: sai kiểu dữ liệu: {err}")
        return None
    except ValueError as err:
        print(f"EAFP: tuổi không hợp lệ: {err}")
        return None
    else:
        print(f"EAFP: tuổi hợp lệ là {age}.")
        return age


def main():
    """Chạy lần lượt bốn ví dụ của bài xử lý ngoại lệ nâng cao."""
    print("1. Chủ động phát sinh ngoại lệ bằng raise")
    for amount in (200_000, 0, 2_000_000):
        # Mỗi ví dụ là một giao dịch độc lập với số dư ban đầu 1 triệu.
        try:
            balance = process_payment("TK001", amount, 1_000_000)
        except (ValueError, PermissionError) as err:
            print(f"{type(err).__name__}: {err}")
        else:
            print(f"Số dư sau giao dịch: {balance:,} đồng.")

    print("\n2. Đọc traceback qua chuỗi gọi main -> service_layer -> data_layer")
    try:
        service_layer()
    except ZeroDivisionError:
        # In traceback thật, nhưng bắt lỗi tại main để tiếp tục các ví dụ.
        traceback.print_exc(file=sys.stdout)
        print(
            "Cách đọc: bắt đầu từ dòng cuối để biết loại lỗi và thông báo, "
            "rồi đọc ngược lên các lời gọi hàm để tìm nơi phát sinh lỗi."
        )

    print("\n3. Kết hợp try - except - else - finally")
    sample_path = Path(__file__).resolve().with_name("payment_data.txt")
    process_data_file(sample_path)

    print("\n4. So sánh LBYL (kiểm tra trước) và EAFP (thử rồi bắt lỗi)")
    samples = (
        ("Thiếu khóa", {}),
        ("Không phải số", {"age": "abc"}),
        ("Tuổi âm", {"age": "-1"}),
        ("Hợp lệ", {"age": "20"}),
    )
    for description, data in samples:
        print(f"\n{description}: {data}")
        get_age_lbyl(data)
        get_age_eafp(data)


if __name__ == "__main__":
    main()
