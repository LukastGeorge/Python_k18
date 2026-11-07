"""Bài 3.2: Truthy/Falsy, vòng lặp có else và biểu thức ternary."""


def test_truthiness(val):
    """In chân trị của val; dùng repr để phân biệt '' với ' '."""
    truth_value = bool(val)
    label = "Truthy" if truth_value else "Falsy"
    print(f"{val!r:>8} -> bool = {str(truth_value):5} -> {label}")


def authenticate_pin():
    """Cho nhập PIN tối đa 3 lần; else chỉ chạy nếu không có break."""
    attempts = 0
    while attempts < 3:
        pin = input(f"Nhập mã PIN (lần {attempts + 1}/3): ")
        attempts += 1
        if pin == "2026":
            print("Đăng nhập thành công!")
            break
        print("Mã PIN không đúng.")
    else:
        print("Tài khoản bị tạm khóa do nhập sai quá 3 lần liên tiếp!")


def calculate_shipping_fee(total_amount):
    """Miễn phí vận chuyển cho đơn hàng từ 500.000 đồng."""
    fee = 0 if total_amount >= 500000 else 30000
    return fee


def find_product(products, target):
    """Minh họa for...else: báo không tìm thấy khi duyệt hết danh sách."""
    for product in products:
        if product == target:
            print(f"Đã tìm thấy: {target}")
            break
    else:
        print(f"Không tìm thấy: {target}")


def main():
    print("1. KHẢO SÁT TRUTHY/FALSY")
    for val in (0.0, "", " ", None, [], [0], {}):
        test_truthiness(val)

    # Chuỗi có dấu cách vẫn Truthy; strip() loại khoảng trắng thừa ở hai đầu.
    name = input("Nhập tên người dùng: ").strip()
    if name:
        print(f"Xin chào, {name}!")
    else:
        print("Bạn chưa nhập tên người dùng.")

    print("\n2. ĐĂNG NHẬP ATM VỚI WHILE...ELSE")
    authenticate_pin()

    print("\n3. PHÍ VẬN CHUYỂN VỚI TERNARY")
    for total_amount in (499999, 500000, 750000):
        fee = calculate_shipping_fee(total_amount)
        print(f"Đơn hàng {total_amount:,.0f} đồng: phí {fee:,.0f} đồng")

    print("\nBỔ SUNG: TÌM KIẾM VỚI FOR...ELSE")
    products = ["Sách", "Bút", "Vở"]
    find_product(products, "Bút")
    find_product(products, "Thước")


if __name__ == "__main__":
    main()
