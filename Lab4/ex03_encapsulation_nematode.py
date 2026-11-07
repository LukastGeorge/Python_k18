"""Bài 3.3: Đóng gói dữ liệu và kiểm tra tính hợp lệ của lớp Nematode."""

from math import isfinite


class Nematode:
    """Mô tả giun tròn với chiều dài (mm), giới tính và tuổi (ngày)."""

    def __init__(self, body_length, gender, age):
        """Khởi tạo các thuộc tính riêng tư sau khi kiểm tra dữ liệu."""
        self._validate_body_length(body_length)
        if not isinstance(gender, str) or gender.lower() not in (
            "hermaphrodite", "male"
        ):
            raise ValueError(
                "Giới tính không hợp lệ "
                "(chỉ chấp nhận 'hermaphrodite' hoặc 'male')!"
            )
        self._validate_age(age)

        self.__body_length = body_length
        self.__gender = gender.lower()
        self.__age = age

    @staticmethod
    def _validate_body_length(body_length):
        """Chiều dài phải là số hữu hạn dương, không chấp nhận bool."""
        if isinstance(body_length, bool) or not isinstance(
            body_length, (int, float)
        ):
            raise TypeError("Chiều dài cơ thể phải có kiểu int hoặc float!")
        # Số nguyên Python luôn hữu hạn; chỉ float có thể là inf hoặc nan.
        if body_length <= 0 or (
            isinstance(body_length, float) and not isfinite(body_length)
        ):
            raise ValueError("Chiều dài cơ thể phải là số thực dương!")

    @staticmethod
    def _validate_age(age):
        """Tuổi phải là số nguyên không âm; bool không được coi là tuổi."""
        if isinstance(age, bool) or not isinstance(age, int) or age < 0:
            raise ValueError("Tuổi cá thể phải là số nguyên không âm!")

    def get_body_length(self):
        """Trả về chiều dài cơ thể tính bằng mm."""
        return self.__body_length

    def get_gender(self):
        """Trả về giới tính đã được chuẩn hóa thành chữ thường."""
        return self.__gender

    def get_age(self):
        """Trả về tuổi cá thể tính bằng ngày."""
        return self.__age

    def set_body_length(self, new_length):
        """Cập nhật chiều dài nếu giá trị mới hợp lệ."""
        self._validate_body_length(new_length)
        self.__body_length = new_length

    def set_age(self, new_age):
        """Cập nhật tuổi; không cho phép tuổi mới nhỏ hơn tuổi hiện tại."""
        self._validate_age(new_age)
        if new_age < self.__age:
            raise ValueError("Tuổi mới không thể nhỏ hơn tuổi hiện tại!")
        self.__age = new_age

    def grow(self, days, length_growth):
        """Tăng tuổi và chiều dài; dữ liệu sai không làm đổi trạng thái."""
        if isinstance(days, bool) or not isinstance(days, int) or days < 0:
            raise ValueError("Số ngày tăng trưởng phải là số nguyên không âm!")
        if isinstance(length_growth, bool) or not isinstance(
            length_growth, (int, float)
        ):
            raise TypeError("Mức tăng chiều dài phải có kiểu int hoặc float!")
        if length_growth < 0 or (
            isinstance(length_growth, float) and not isfinite(length_growth)
        ):
            raise ValueError("Mức tăng chiều dài phải là số hữu hạn không âm!")

        # Tính và kiểm tra trước khi gán để tránh chỉ cập nhật một thuộc tính.
        try:
            new_length = self.__body_length + length_growth
        except OverflowError as err:
            raise ValueError("Chiều dài sau tăng trưởng quá lớn!") from err
        self._validate_body_length(new_length)
        new_age = self.__age + days
        self.__body_length = new_length
        self.__age = new_age

    def __str__(self):
        """Trả thông tin dễ đọc khi dùng print() hoặc str()."""
        return (
            f"Nematode(Length: {self.__body_length}mm, "
            f"Gender: {self.__gender}, Age: {self.__age} days)"
        )

    def __repr__(self):
        """Trả biểu diễn giống câu lệnh khởi tạo để hỗ trợ kiểm tra lỗi."""
        return (
            f"Nematode({self.__body_length}, "
            f"'{self.__gender}', {self.__age})"
        )


def main():
    """Minh họa getter, setter, name mangling và xử lý dữ liệu không hợp lệ."""
    print("NHIỆM VỤ 1: KHỞI TẠO VÀ TRUY CẬP QUA GETTER")
    n1 = Nematode(1.05, "hermaphrodite", 3)
    print("Chiều dài:", n1.get_body_length(), "mm")
    print("Giới tính:", n1.get_gender())
    print("Tuổi:", n1.get_age(), "ngày")
    print("str(n1):", str(n1))
    print("repr(n1):", repr(n1))

    print("\nNHIỆM VỤ 2: THUỘC TÍNH RIÊNG TƯ VÀ NAME MANGLING")
    try:
        print(n1.__body_length)
    except AttributeError as err:
        print(f"Không truy cập trực tiếp được: {err}")
    print("Đọc qua tên đã biến đổi:", n1._Nematode__body_length)
    print(
        "Python đổi __body_length thành _Nematode__body_length để hạn chế "
        "truy cập nhầm. Đây không phải cơ chế bảo mật tuyệt đối."
    )
    print("Khi sử dụng lớp, nên đọc và cập nhật qua getter/setter.")

    print("\nNHIỆM VỤ 3: TĂNG TRƯỞNG VÀ CẬP NHẬT HỢP LỆ")
    n1.grow(2, 0.15)
    print("Sau grow(2, 0.15):", n1)
    n1.set_body_length(1.3)
    n1.set_age(6)
    print("Sau set_body_length(1.3) và set_age(6):", n1)
    print("Chuẩn hóa giới tính:", Nematode(0.8, "MALE", 0))

    print("\nNHIỆM VỤ 4: BẮT LỖI DỮ LIỆU KHÔNG HỢP LỆ")
    invalid_operations = [
        ("Chiều dài bằng 0", lambda: Nematode(0, "male", 0)),
        ("Chiều dài sai kiểu", lambda: Nematode("1.05", "male", 0)),
        ("Giới tính không hợp lệ", lambda: Nematode(1.05, "female", 0)),
        ("Tuổi không nguyên", lambda: Nematode(1.05, "male", 1.5)),
        ("Setter chiều dài âm", lambda: n1.set_body_length(-1)),
        ("Setter tuổi âm", lambda: n1.set_age(-1)),
        ("Setter giảm tuổi", lambda: n1.set_age(2)),
        ("Số ngày âm", lambda: n1.grow(-1, 0.1)),
        ("Mức tăng chiều dài âm", lambda: n1.grow(1, -0.1)),
        ("Mức tăng không hữu hạn", lambda: n1.grow(1, float("inf"))),
    ]
    for description, operation in invalid_operations:
        try:
            operation()
        except (TypeError, ValueError) as err:
            print(f"{description} -> {type(err).__name__}: {err}")
    print("Trạng thái sau các lần cập nhật bị từ chối:", n1)


if __name__ == "__main__":
    main()
