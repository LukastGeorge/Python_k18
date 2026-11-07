"""Bài 4: Kiểm tra dữ liệu nhập, thanh tiến trình và ký tự thoát."""

import time


def get_valid_integer(prompt, min_val, max_val):
    """Nhập lại đến khi nhận được số nguyên trong đoạn [min_val, max_val]."""
    while True:
        user_input = input(prompt).strip()
        try:
            # int() chấp nhận cả số nguyên âm, ví dụ -5.
            number = int(user_input)
        except ValueError:
            print("Dữ liệu không hợp lệ. Vui lòng nhập một số nguyên.")
            continue

        if min_val <= number <= max_val:
            return number

        print(f"Vui lòng nhập số nguyên từ {min_val} đến {max_val}.")


def get_valid_name(prompt):
    """Nhập lại đến khi tên không rỗng và chỉ chứa chữ cái, dấu cách."""
    while True:
        name = input(prompt).strip()
        # isalpha() nhận biết cả chữ cái tiếng Việt có dấu.
        if name and name.replace(" ", "").isalpha():
            return name

        print("Tên không được để trống và chỉ được chứa chữ cái, dấu cách.")


def main():
    name = get_valid_name("Nhập họ và tên: ")
    number = get_valid_integer("Nhập số nguyên từ -10 đến 100: ", -10, 100)
    print(f"Xin chào {name}! Số nguyên hợp lệ bạn vừa nhập là {number}.")
    print("Kết quả", name, number, sep=" | ")

    print("Mô phỏng thanh tiến trình:")
    for step in range(11):
        progress_bar = "#" * step + "-" * (10 - step)
        # \r đưa con trỏ về đầu dòng; end="" không xuống dòng.
        print(f"\rTiến độ: [{progress_bar}] {step * 10:3d}%", end="", flush=True)
        time.sleep(0.3)
    print("\nHoàn thành!")

    print("\nVí dụ về các ký tự thoát:")
    print("Xuống dòng bằng \\n: Dòng thứ nhất\nDòng thứ hai")
    print("Tab bằng \\t: Họ tên\tĐiểm")
    print('Dấu nháy đơn bằng \\\': \'Xin chào!\'')
    print("Dấu gạch chéo ngược bằng \\\\: \\")

    # Chuỗi thường diễn giải \n và \t thành xuống dòng và tab.
    normal_path = "C:\new_folder\test.txt"
    # Tiền tố r giữ nguyên dấu gạch chéo ngược trong đường dẫn Windows.
    raw_path = r"C:\new_folder\test.txt"
    print("\nĐường dẫn Windows trong chuỗi thường:")
    print(normal_path)
    print("Đường dẫn Windows trong raw string:")
    print(raw_path)


if __name__ == "__main__":
    main()
