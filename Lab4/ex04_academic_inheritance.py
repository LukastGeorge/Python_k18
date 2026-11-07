"""Bài 3.4: Kế thừa và đa hình trong hệ thống quản lý thành viên học thuật."""


class Member:
    """Lưu thông tin chung của một thành viên trong trường."""

    def __init__(self, member_id, name, email):
        self.member_id = member_id
        self.name = name
        self.email = email

    def get_role(self):
        """Trả về vai trò mặc định của thành viên."""
        return "Thành viên chung"

    def get_details(self):
        """Trả về thông tin chung dưới dạng chuỗi."""
        return (
            f"Mã: {self.member_id} | Họ tên: {self.name} "
            f"| Email: {self.email}"
        )

    def __str__(self):
        # Phương thức của lớp con vẫn được gọi khi lớp con ghi đè get_details.
        return self.get_details()

    def __repr__(self):
        return (
            f"Member({self.member_id!r}, {self.name!r}, {self.email!r})"
        )


class Student(Member):
    """Bổ sung ngành học, GPA và các môn học cho thành viên sinh viên."""

    def __init__(self, member_id, name, email, major, gpa=0.0):
        super().__init__(member_id, name, email)
        self.major = major
        self.gpa = gpa
        # Mỗi sinh viên có hai danh sách riêng, không dùng chung giữa đối tượng.
        self.courses_taken = []
        self.current_courses = []

    def enroll_course(self, course_name):
        """Thêm môn học vào danh sách đang học."""
        self.current_courses.append(course_name)

    def complete_course(self, course_name):
        """Chuyển môn đang học sang danh sách hoàn thành nếu môn tồn tại."""
        if course_name in self.current_courses:
            self.current_courses.remove(course_name)
            self.courses_taken.append(course_name)

    def get_role(self):
        return "Sinh viên Đại học"

    def get_details(self):
        """Mở rộng thông tin thành viên bằng thông tin học tập."""
        return (
            super().get_details()
            + f" | Ngành: {self.major} | GPA: {self.gpa}"
            + f" | Đang học: {len(self.current_courses)} môn"
        )

    def __repr__(self):
        return (
            f"Student({self.member_id!r}, {self.name!r}, "
            f"{self.email!r}, {self.major!r}, {self.gpa!r})"
        )


class Faculty(Member):
    """Bổ sung khoa, học vị và các môn giảng dạy cho giảng viên."""

    def __init__(self, member_id, name, email, department, academic_rank):
        super().__init__(member_id, name, email)
        self.department = department
        self.academic_rank = academic_rank
        self.teaching_courses = []

    def assign_course(self, course_name):
        """Thêm môn học vào danh sách được phân công giảng dạy."""
        self.teaching_courses.append(course_name)

    def get_role(self):
        return "Giảng viên Khoa"

    def get_details(self):
        """Mở rộng thông tin thành viên bằng thông tin giảng dạy."""
        return (
            super().get_details()
            + f" | Học vị: {self.academic_rank} | Khoa: {self.department}"
            + f" | Các môn giảng dạy: {', '.join(self.teaching_courses)}"
        )

    def __repr__(self):
        return (
            f"Faculty({self.member_id!r}, {self.name!r}, "
            f"{self.email!r}, {self.department!r}, {self.academic_rank!r})"
        )


def main():
    """Minh họa ghi đè phương thức, đa hình và quan hệ kế thừa."""
    student = Student(
        "SV01", "Nguyen Van An", "an.nv@gdu.edu.vn", "Kỹ thuật phần mềm", 3.65
    )
    faculty = Faculty(
        "GV01", "TS. Tran Minh Quang", "quang.tm@gdu.edu.vn",
        "Khoa CNTT", "Tiến sĩ"
    )
    member = Member("MB01", "Le Thi Hoa", "hoa.lt@gdu.edu.vn")

    student.enroll_course("Lập trình Python")
    student.enroll_course("Cơ sở dữ liệu")
    faculty.assign_course("Lập trình Python")
    members = [student, faculty, member]

    print("=== ĐA HÌNH: CÙNG LỜI GỌI, KHÁC CÁCH THỰC HIỆN ===")
    # Không cần xét kiểu đối tượng: Python chọn phương thức phù hợp tự động.
    for person in members:
        print("Vai trò:", person.get_role())
        print(person.get_details())

    print("\n=== HOÀN THÀNH MÔN HỌC ===")
    student.complete_course("Lập trình Python")
    print("Môn đang học:", student.current_courses)
    print("Môn đã hoàn thành:", student.courses_taken)
    print("Thông tin qua __str__:", student)

    print("\n=== KIỂM TRA QUAN HỆ KẾ THỪA ===")
    print("isinstance(student, Member):", isinstance(student, Member))
    print("issubclass(Student, Member):", issubclass(Student, Member))
    print("issubclass(Faculty, Member):", issubclass(Faculty, Member))
    print("Student.mro():", [cls.__name__ for cls in Student.mro()])

    print("\n=== BIỂU DIỄN ĐỐI TƯỢNG QUA __repr__ ===")
    # Khi in list, Python dùng __repr__ của từng phần tử.
    print(members)


if __name__ == "__main__":
    main()
