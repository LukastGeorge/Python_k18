"""Bài 3.4: Thao tác từ điển, báo cáo kho, thống kê và dict comprehension."""


def count_keywords(keywords):
    """Đếm số lần xuất hiện của từng từ khóa bằng setdefault()."""
    freq_dict = {}
    for word in keywords:
        freq_dict.setdefault(word, 0)
        freq_dict[word] += 1
    return freq_dict


def group_students(students_data):
    """Gom tên sinh viên vào danh sách của từng ngành bằng setdefault()."""
    grouped_students = {}
    for major, name in students_data:
        grouped_students.setdefault(major, []).append(name)
    return grouped_students


def main():
    print("NHIỆM VỤ 1: THAO TÁC CƠ BẢN VÀ TRUY CẬP AN TOÀN")
    inventory = {"cpu": 12, "ram": 45, "ssd": 30, "gpu": 8, "mainboard": 15}
    print("Kho ban đầu:", inventory)
    inventory["psu"] = 20
    inventory["ram"] = 50
    print("Kho sau khi thêm psu và cập nhật ram:", inventory)

    try:
        print("Số lượng monitor:", inventory["monitor"])
    except KeyError as err:
        print(f"Truy cập trực tiếp khóa thiếu gây KeyError: {err}")
    print("inventory.get('monitor', 0):", inventory.get("monitor", 0))

    for item in ("cpu", "case"):
        if item in inventory:
            print(f"Linh kiện {item} có trong kho.")
        else:
            print(f"Linh kiện {item} chưa có trong kho.")
    print("Các khóa qua keys():", list(inventory.keys()))
    print("Các số lượng qua values():", list(inventory.values()))
    print("Khóa phải hashable; tên linh kiện là chuỗi bất biến nên dùng làm khóa được.")

    print("\nNHIỆM VỤ 2: BÁO CÁO GIÁ TRỊ TỒN KHO")
    unit_prices = {
        "cpu": 4500000,
        "ram": 950000,
        "ssd": 1200000,
        "gpu": 8500000,
        "mainboard": 2800000,
        "psu": 1500000,
    }
    print(f"{'Linh kiện':<12}{'Số lượng':>10}{'Đơn giá (VNĐ)':>20}{'Thành tiền (VNĐ)':>22}")
    print("-" * 64)
    total_value = 0
    item_values = {}
    for item, qty in inventory.items():
        unit_price = unit_prices[item]
        item_value = qty * unit_price
        item_values[item] = item_value
        total_value += item_value
        print(f"{item:<12}{qty:>10}{unit_price:>20,}{item_value:>22,}")
    print("-" * 64)
    print(f"Tổng giá trị kho: {total_value:,} VNĐ")

    # max() so sánh giá trị tồn kho, rồi trả về khóa tương ứng.
    most_valuable_item = max(item_values, key=item_values.get)
    print(
        f"Linh kiện có giá trị tồn kho lớn nhất: {most_valuable_item} "
        f"({item_values[most_valuable_item]:,} VNĐ)"
    )

    print("\nNHIỆM VỤ 3: THỐNG KÊ TẦN SUẤT VÀ GOM NHÓM")
    keywords = [
        "python", "ai", "django", "python", "fastapi",
        "ai", "python", "docker", "ai", "pandas",
    ]
    freq_dict = count_keywords(keywords)
    print("Tần suất từ khóa:", freq_dict)

    students_data = [
        ("KTPM", "Tran An"),
        ("CNTT", "Le Binh"),
        ("KTPM", "Hoang Chi"),
        ("ATTT", "Pham Dung"),
        ("CNTT", "Nguyen Hoa"),
        ("ATTT", "Do Khoa"),
    ]
    grouped_students = group_students(students_data)
    print("Sinh viên theo ngành:", grouped_students)

    print("\nNHIỆM VỤ 4: DICT COMPREHENSION")
    raw_grades = {"An": 8.5, "Binh": 6.0, "Chi": 9.5, "Dung": 4.5, "Hoa": 7.5, "Khoa": 3.5}
    gpa_scale_4 = {name: round(grade * 0.4, 2) for name, grade in raw_grades.items()}
    excellent_students = {name: grade for name, grade in raw_grades.items() if grade >= 8.0}
    print("Điểm thang 10:", raw_grades)
    print("Điểm quy đổi thang 4:", gpa_scale_4)
    print("Sinh viên đạt từ 8.0:", excellent_students)

    error_codes = {200: "OK", 404: "Not Found", 500: "Internal Server Error"}
    reversed_errors = {message: code for code, message in error_codes.items()}
    print("Mã lỗi ban đầu:", error_codes)
    print("Đảo ngược khóa và giá trị:", reversed_errors)


if __name__ == "__main__":
    main()
