"""Bài 3.1: Phép toán chuỗi, phép gán và so sánh số thực."""

import math


def is_equal_float(a, b, epsilon=1e-9):
    """Trả về True nếu độ lệch tuyệt đối giữa a và b nhỏ hơn epsilon."""
    return abs(a - b) < epsilon


def main():
    # 1. Nhân bản và nối chuỗi.
    title = "TRƯỜNG ĐẠI HỌC GIA ĐỊNH"
    print("=" * 40)
    print(title)
    print("=" * 40)

    # 'GDU khóa ' + 2026 gây TypeError vì không thể nối str với int.
    print("Dùng str():", "GDU khóa " + str(2026))
    print("Dùng f-string:", f"GDU khóa {2026}")

    # 2. Gán đồng thời, hoán đổi xoay vòng và gán chuỗi.
    x, y, z = 10, -25, 0
    print(f"Tọa độ: x = {x}, y = {y}, z = {z}")

    a, b, c = 1, 2, 3
    print(f"Trước hoán đổi: a = {a}, b = {b}, c = {c}")
    a, b, c = b, c, a
    print(f"Sau hoán đổi: a = {a}, b = {b}, c = {c}")

    count_a = count_b = count_c = 0
    print("Ba bộ đếm:", count_a, count_b, count_c)
    count_a += 1  # Toán tử gán mở rộng, tương đương count_a = count_a + 1.
    print("Sau count_a += 1:", count_a, count_b, count_c)

    # None biểu diễn trạng thái chưa có giá trị; kiểm tra bằng is None.
    result = None
    print("Kiểu của result:", type(result).__name__)
    if result is None:
        print("result chưa có giá trị.")

    # 3. Cạm bẫy so sánh số thực.
    print("0.1 + 0.2 =", 0.1 + 0.2)
    print("0.1 + 0.2 == 0.3:", 0.1 + 0.2 == 0.3)
    print(
        "Nhận xét: kết quả là False vì 0.1 và 0.2 không được biểu diễn "
        "chính xác bằng số thực nhị phân; tổng có sai số rất nhỏ."
    )
    print("So sánh với epsilon:", is_equal_float(0.1 + 0.2, 0.3))
    print("So sánh bằng math.isclose():", math.isclose(0.1 + 0.2, 0.3))


if __name__ == "__main__":
    main()
