"""Bài 3.2: Tuple, tính bất biến, unpacking và tham số *args."""


def analyze_numbers(numbers_list):
    """Trả tuple (nhỏ nhất, lớn nhất, trung bình) của danh sách không rỗng.

    Raises:
        ValueError: Nếu danh sách rỗng nên không thể tính các thống kê.
    """
    if not numbers_list:
        raise ValueError("Danh sách số không được rỗng!")
    return min(numbers_list), max(numbers_list), sum(numbers_list) / len(numbers_list)


def calculate_polygon_perimeter(*edges):
    """Trả tổng các cạnh; yêu cầu ít nhất 3 cạnh và mỗi cạnh lớn hơn 0."""
    if len(edges) < 3:
        raise ValueError("Đa giác phải có ít nhất 3 cạnh!")
    if any(edge <= 0 for edge in edges):
        raise ValueError("Độ dài cạnh phải là số dương!")
    return sum(edges)


def main():
    print("NHIỆM VỤ 1: KHỞI TẠO TUPLE VÀ TÍNH BẤT BIẾN")
    single_wrong = ("GDU")
    single_correct = ("GDU",)
    print("single_wrong:", single_wrong, "- kiểu:", type(single_wrong))
    print("single_correct:", single_correct, "- kiểu:", type(single_correct))
    print("Dấu phẩy mới tạo tuple một phần tử; chỉ dấu ngoặc là chưa đủ.")

    gdu_location = (10.8062, 106.6661, "371 Nguyen Kiem, Go Vap, TP.HCM")
    print("Tọa độ ban đầu:", gdu_location)
    try:
        gdu_location[0] = 10.8100
    except TypeError as err:
        print(f"TypeError: {err}")

    # Tạo tuple mới qua list trung gian, không sửa trực tiếp tuple cũ.
    location_list = list(gdu_location)
    location_list[0] = 10.8100
    gdu_location = tuple(location_list)
    print("Tọa độ sau cập nhật gián tiếp:", gdu_location)

    print("\nNHIỆM VỤ 2: EXTENDED UNPACKING VÀ HOÁN ĐỔI")
    student_record = (
        "2211005", "Nguyen Van Binh", 8.5, 9.0, 7.5, 8.0, "Kỹ thuật phần mềm"
    )
    student_id, full_name, *exam_scores, major = student_record
    print("Mã sinh viên:", student_id)
    print("Họ tên:", full_name)
    print("Danh sách điểm:", exam_scores)
    print("Kiểu của exam_scores:", type(exam_scores))
    print("Chuyên ngành:", major)
    print(f"Điểm trung bình: {sum(exam_scores) / len(exam_scores):.2f}")

    a, b, c = 100, 200, 300
    a, b, c = b, c, a
    print(f"Sau hoán đổi xoay vòng: a = {a}, b = {b}, c = {c}")

    print("\nNHIỆM VỤ 3: TRẢ NHIỀU GIÁ TRỊ VÀ NHẬN *ARGS")
    min_val, max_val, avg_val = analyze_numbers([12, 45, 67, 23, 89, 34])
    print(f"min_val = {min_val}, max_val = {max_val}, avg_val = {avg_val}")
    print("Chu vi tam giác (3, 4, 5):", calculate_polygon_perimeter(3, 4, 5))
    print("Chu vi tứ giác (2, 3, 4, 5):", calculate_polygon_perimeter(2, 3, 4, 5))
    print("Chu vi ngũ giác (2, 3, 4, 5, 6):", calculate_polygon_perimeter(2, 3, 4, 5, 6))

    for invalid_edges in ((5, 10), (3, -4, 5), (3, 0, 5)):
        try:
            calculate_polygon_perimeter(*invalid_edges)
        except ValueError as err:
            print(f"Các cạnh {invalid_edges} -> ValueError: {err}")


if __name__ == "__main__":
    main()
