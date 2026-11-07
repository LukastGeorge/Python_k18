"""Bài 3: Thiết kế hàm tính lãi kép và sử dụng docstring."""


def calculate_compound_interest(principal, annual_rate, years, compound_freq=12):
    
    return principal * (1 + annual_rate / compound_freq) ** (compound_freq * years)


def main():
    # Hai cách xem tài liệu của hàm.
    print("Tài liệu hiển thị bằng help():")
    help(calculate_compound_interest)

    print("Docstring lấy từ thuộc tính __doc__:")
    print(calculate_compound_interest.__doc__)

    # Truyền đối số theo vị trí; bỏ compound_freq để dùng mặc định 12.
    amount_positional = calculate_compound_interest(100000000, 0.07, 5)

    # Truyền đối số theo tên nên có thể thay đổi thứ tự đối số.
    amount_keyword = calculate_compound_interest(
        years=5, principal=100000000, annual_rate=0.07
    )

    # Ghi đè giá trị mặc định: nhập lãi một lần mỗi năm.
    amount_yearly = calculate_compound_interest(
        100000000, 0.07, 5, compound_freq=1
    )

    print("Gửi 100.000.000 đồng, lãi suất 7%/năm trong 5 năm:")
    print(f"Đối số vị trí, nhập lãi hàng tháng: {amount_positional:,.2f} đồng")
    print(f"Đối số theo tên, nhập lãi hàng tháng: {amount_keyword:,.2f} đồng")
    print(f"Nhập lãi hàng năm (compound_freq=1): {amount_yearly:,.2f} đồng")


if __name__ == "__main__":
    main()
