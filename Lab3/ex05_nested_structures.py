"""Bài 5: Quản lý giỏ hàng bằng dictionary và list lồng nhau."""

import pprint


ecommerce_system = {
    "CUST01": {
        "name": "Nguyễn Văn An",
        "email": "an.nv@gmail.com",
        "is_vip": True,
        "cart": [
            {
                "id": "SP01",
                "name": "Bàn phím cơ Akko",
                "price": 1250000,
                "qty": 1,
            },
            {
                "id": "SP02",
                "name": "Chuột Logitech G102",
                "price": 450000,
                "qty": 2,
            },
        ],
    },
    "CUST02": {
        "name": "Trần Thị Bình",
        "email": "binh.tt@gmail.com",
        "is_vip": False,
        "cart": [
            {
                "id": "SP04",
                "name": "Màn hình Dell 24 inch",
                "price": 4000000,
                "qty": 1,
            }
        ],
    },
    "CUST03": {
        "name": "Lê Minh Châu",
        "email": "chau.lm@gmail.com",
        "is_vip": True,
        "cart": [
            {
                "id": "SP05",
                "name": "Ghế công thái học",
                "price": 4200000,
                "qty": 1,
            }
        ],
    },
}


def calculate_customer_bill(system_data, customer_id):
    """Trả về (tổng tiền gốc, tiền phải trả); mã không tồn tại trả (0, 0)."""
    if customer_id not in system_data:
        return (0, 0)

    customer = system_data[customer_id]
    total = 0
    for product in customer["cart"]:
        total += product["price"] * product["qty"]

    amount_to_pay = total
    if customer["is_vip"]:
        amount_to_pay = total * 0.9

    return (total, amount_to_pay)


def add_product_to_cart(system_data, customer_id, new_product):
    """Tăng số lượng nếu trùng mã; nếu chưa có, thêm trực tiếp new_product."""
    if customer_id not in system_data:
        raise KeyError(f"Không tìm thấy khách hàng có mã {customer_id}.")

    cart = system_data[customer_id]["cart"]
    for product in cart:
        if product["id"] == new_product["id"]:
            product["qty"] += new_product["qty"]
            return

    cart.append(new_product)


def find_top_spender(system_data):
    """Trả (mã, tên, tiền phải trả) cao nhất; hệ thống rỗng trả None.

    Nếu bằng tiền nhau, chọn khách hàng xuất hiện trước trong dictionary.
    """
    top_spender = None
    for customer_id, customer in system_data.items():
        total, amount_to_pay = calculate_customer_bill(system_data, customer_id)
        if top_spender is None or amount_to_pay > top_spender[2]:
            top_spender = (customer_id, customer["name"], amount_to_pay)

    return top_spender


def main():
    print("=== BÀI 5: QUẢN LÝ GIỎ HÀNG ===")

    # Tính hóa đơn trước khi thay đổi giỏ hàng CUST01.
    total, amount_to_pay = calculate_customer_bill(ecommerce_system, "CUST01")
    print("Hóa đơn ban đầu của Nguyễn Văn An:")
    print(f"Tổng tiền gốc: {total:,.0f} đồng")
    print(f"Sau giảm giá VIP 10%: {amount_to_pay:,.0f} đồng")

    # Sản phẩm đã có: chỉ cộng thêm số lượng.
    add_product_to_cart(
        ecommerce_system,
        "CUST01",
        {
            "id": "SP02",
            "name": "Chuột Logitech G102",
            "price": 450000,
            "qty": 1,
        },
    )
    for product in ecommerce_system["CUST01"]["cart"]:
        if product["id"] == "SP02":
            print(f"Số lượng SP02 sau khi thêm: {product['qty']} (ban đầu: 2)")

    # Sản phẩm mới: thêm dictionary này trực tiếp vào danh sách giỏ hàng.
    new_product = {
        "id": "SP03",
        "name": "Tai nghe Sony",
        "price": 1800000,
        "qty": 1,
    }
    add_product_to_cart(ecommerce_system, "CUST01", new_product)
    print("Đã thêm SP03 - Tai nghe Sony vào giỏ hàng CUST01.")

    total, amount_to_pay = calculate_customer_bill(ecommerce_system, "CUST01")
    print(f"Hóa đơn CUST01 sau cập nhật: {total:,.0f} đồng")
    print(f"CUST01 phải trả sau giảm giá: {amount_to_pay:,.0f} đồng")

    top_spender = find_top_spender(ecommerce_system)
    if top_spender is not None:
        customer_id, name, amount = top_spender
        print(f"Khách chi tiêu cao nhất: {customer_id} - {name}: {amount:,.0f} đồng")

    print("\nIn toàn bộ hệ thống bằng print:")
    print(ecommerce_system)
    print("\nIn toàn bộ hệ thống bằng pprint:")
    pprint.pprint(ecommerce_system, indent=4, width=70)


if __name__ == "__main__":
    main()
