"""Bài 3.1: Thao tác list, bí danh, sao chép và list comprehension."""

import copy


def main():
    print("NHIỆM VỤ 1: QUẢN LÝ DANH SÁCH ĐIỂM")
    scores = [7.5, 8.0, 6.5, 9.0, 8.5, 7.0, 9.5]
    print("Điểm ban đầu:", scores)

    scores.insert(2, 8.75)
    scores.append(10.0)
    scores.remove(6.5)
    last_score = scores.pop()
    print("Điểm cuối vừa lấy ra (last_score):", last_score)
    print("Danh sách sau CRUD:", scores)

    print("Ba điểm đầu:", scores[:3])
    print("Ba điểm cuối:", scores[-3:])
    print("Đảo ngược danh sách:", scores[::-1])

    # sort() sửa trực tiếp list; sorted() trả về một list mới.
    scores.sort(reverse=True)
    print("scores sau sort(reverse=True):", scores)
    ascending_scores = sorted(scores)
    print("List tăng dần mới từ sorted():", ascending_scores)
    print("scores vẫn giữ thứ tự giảm dần:", scores)

    print("\nNHIỆM VỤ 2: BÍ DANH VÀ THAM CHIẾU")
    original_list = [10, 20, 30]
    alias_list = original_list
    alias_list[0] = 99
    print("original_list:", original_list)
    print("alias_list:", alias_list)
    print("id(original_list):", id(original_list))
    print("id(alias_list):", id(alias_list))
    print("Hai id bằng nhau:", id(original_list) == id(alias_list))
    print("Phép gán không sao chép list: hai biến cùng tham chiếu một đối tượng.")

    print("\nNHIỆM VỤ 3: MA TRẬN, SHALLOW COPY VÀ DEEP COPY")
    grid_wrong = [["-"] * 3] * 3
    grid_correct = [["-"] * 3 for _ in range(3)]
    grid_wrong[0][0] = "X"
    grid_correct[0][0] = "X"

    print("grid_wrong (cả ba dòng cùng thay đổi):")
    for row in grid_wrong:
        print(row)
    print("grid_correct (chỉ ô [0][0] thay đổi):")
    for row in grid_correct:
        print(row)
    print(
        "Nhân list ngoài bằng 3 lặp lại tham chiếu đến cùng một list con. "
        "Comprehension tạo một list con mới ở mỗi lượt lặp."
    )

    nested_data = [[1, 2], [3, 4]]
    shallow_data = copy.copy(nested_data)
    deep_data = copy.deepcopy(nested_data)
    nested_data[0][0] = 999
    print("nested_data:", nested_data)
    print("shallow_data:", shallow_data)
    print("deep_data:", deep_data)
    print(
        "Shallow copy chỉ sao chép list ngoài nên vẫn dùng chung các list con. "
        "Deep copy sao chép cả các list con nên giữ được giá trị ban đầu."
    )

    print("\nNHIỆM VỤ 4: LIST COMPREHENSION")
    raw_scores = [3.5, 7.0, 8.5, 4.0, 9.5, 6.0, 5.5, 2.0, 10.0]
    passed_scores = [score for score in raw_scores if score >= 5.0]
    bonus_scores = [min(score + 0.5, 10.0) for score in raw_scores]
    status_labels = ["Đạt" if score >= 5.0 else "Không đạt" for score in raw_scores]
    print("Điểm gốc:", raw_scores)
    print("Điểm đạt:", passed_scores)
    print("Điểm sau cộng ưu tiên (tối đa 10):", bonus_scores)
    print("Nhãn kết quả:", status_labels)

    # Minh họa thêm các lỗi thường gặp trong mục tiêu bài học.
    print("\nBỔ SUNG: THAO TÁC LIST AN TOÀN")
    try:
        print(scores[len(scores)])  # Chỉ số cuối hợp lệ là len(scores) - 1.
    except IndexError as err:
        print(f"IndexError: {err}")
    try:
        scores.remove(6.5)  # Điểm này đã được xóa ở nhiệm vụ 1.
    except ValueError as err:
        print(f"ValueError: {err}")
    print("Nên kiểm tra chỉ số hợp lệ và dùng 'value in scores' trước khi remove.")


if __name__ == "__main__":
    main()
