"""Bài 3.3: Tập hợp, đại số tập hợp, set comprehension và frozenset."""


def main():
    print("NHIỆM VỤ 1: KHỞI TẠO SET, LỌC TRÙNG VÀ XÓA PHẦN TỬ")
    obj_a = {}
    obj_b = set()
    print("Kiểu của {}:", type(obj_a))
    print("Kiểu của set():", type(obj_b))

    raw_user_ids = [101, 105, 102, 101, 108, 105, 102, 109, 101, 110]
    clean_user_ids = list(set(raw_user_ids))
    clean_user_ids.sort()
    print("ID ban đầu:", raw_user_ids)
    print("ID đã lọc trùng và sắp xếp:", clean_user_ids)
    print("Set không có thứ tự; cần sắp xếp danh sách để có thứ tự tăng dần.")

    skills = {"Python", "SQL", "Git"}
    print("Kỹ năng ban đầu:", skills)
    skills.add("Docker")
    print("Sau add('Docker'):", skills)
    skills.update(["FastAPI", "SQL", "Linux"])
    print("Sau update:", skills)
    print("Có", len(skills), "kỹ năng; SQL chỉ xuất hiện một lần.")

    skills.discard("Kubernetes")
    print("discard('Kubernetes') không gây lỗi dù phần tử không tồn tại.")
    try:
        skills.remove("Kubernetes")
    except KeyError as err:
        print(f"remove('Kubernetes') gây KeyError: {err}")

    print("\nNHIỆM VỤ 2: ĐẠI SỐ TẬP HỢP VỚI CÁC CÂU LẠC BỘ")
    club_ai = {"An", "Binh", "Chi", "Dung", "Hoa", "Khoa"}
    club_web = {"Binh", "Dung", "Hanh", "Khoa", "Lan", "Mai"}
    club_devops = {"Chi", "Dung", "Khoa", "Minh", "Nam", "Lan"}

    union_members = club_ai | club_web
    intersection_members = club_ai & club_web
    ai_only_members = club_ai - club_web
    symmetric_difference_members = club_ai ^ club_web
    all_three_members = club_ai & club_web & club_devops

    # sorted() giúp kết quả hiển thị ổn định; kết quả phép toán vẫn là set.
    print("Hợp AI | Web:", sorted(union_members))
    print("Số sinh viên trong hợp:", len(union_members))
    print("Giao AI & Web:", sorted(intersection_members))
    print("Hiệu AI - Web:", sorted(ai_only_members))
    print("Hiệu đối xứng AI ^ Web:", sorted(symmetric_difference_members))
    print("Giao cả ba câu lạc bộ:", sorted(all_three_members))

    group = {"Binh", "Khoa"}
    other_students = {"Phuong", "Quang"}
    print("Nhóm Binh, Khoa là tập con của Web:", group.issubset(club_web))
    print("Web là tập cha của nhóm Binh, Khoa:", club_web.issuperset(group))
    print("AI rời nhau với nhóm Phuong, Quang:", club_ai.isdisjoint(other_students))

    print("\nNHIỆM VỤ 3: SET COMPREHENSION VÀ FROZENSET")
    text = "lap trinh ngon ngu python voi du lieu collection tai truong dai hoc gia dinh"
    even_ascii_chars = {char for char in text if char.isalpha() and ord(char) % 2 == 0}
    print("Các chữ cái duy nhất có mã ASCII chẵn:", even_ascii_chars)
    print("Các chữ cái theo thứ tự:", sorted(even_ascii_chars))
    print("Số lượng chữ cái:", len(even_ascii_chars))

    admin_roles = frozenset(["CREATE", "READ", "UPDATE", "DELETE"])
    viewer_roles = frozenset(["READ"])
    security_matrix = {
        admin_roles: "Toàn quyền Quản trị (SuperAdmin)",
        viewer_roles: "Quyền Chỉ đọc (Guest)",
    }
    print("Quyền của admin:", security_matrix[admin_roles])
    print("Quyền của viewer:", security_matrix[viewer_roles])
    print(
        "Khóa dict phải hashable: có giá trị băm ổn định. "
        "Set thay đổi được và không hashable nên không thể làm khóa; "
        "frozenset bất biến, hashable nên có thể làm khóa."
    )
    try:
        invalid_matrix = {set(admin_roles): "Quản trị"}
    except TypeError as err:
        print(f"Dùng set làm khóa gây TypeError: {err}")


if __name__ == "__main__":
    main()
