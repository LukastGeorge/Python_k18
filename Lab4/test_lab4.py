"""Kiểm thử kết quả trong đề và các trường hợp biên của bốn bài Lab4."""

import unittest

from ex01_country_class import Country
from ex02_continent_composition import Continent
from ex03_encapsulation_nematode import Nematode
from ex04_academic_inheritance import Faculty, Member, Student


class CountryTests(unittest.TestCase):
    def setUp(self):
        self.canada = Country("Canada", 34482779, 9984670)

    def test_sample_attributes_and_density(self):
        self.assertEqual(self.canada.name, "Canada")
        self.assertEqual(self.canada.population, 34482779)
        self.assertEqual(self.canada.area, 9984670)
        self.assertAlmostEqual(
            self.canada.population_density(), 3.4535722262227995
        )
        self.assertEqual(Country("Empty", 0, 10).population_density(), 0.0)

    def test_area_comparison(self):
        usa = Country("United States of America", 313914040, 9826675)
        vietnam = Country("Vietnam", 98000000, 331212)
        self.assertTrue(self.canada.is_larger(usa))
        self.assertFalse(vietnam.is_larger(self.canada))
        self.assertFalse(self.canada.is_larger(self.canada))
        with self.assertRaises(TypeError):
            self.canada.is_larger("USA")

    def test_invalid_population_and_area(self):
        for population, area in ((-100, 500), (100, -10), (100, 0),
                                 (100, float("nan")), (100, float("inf"))):
            with self.subTest(population=population, area=area):
                with self.assertRaises(ValueError):
                    Country("X", population, area)

    def test_invalid_types(self):
        for args in ((1, 100, 10), ("X", 1.5, 10), ("X", True, 10),
                     ("X", 100, "10"), ("X", 100, True)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    Country(*args)

    def test_string_representations(self):
        self.assertEqual(
            str(self.canada),
            "Canada has a population of 34482779 and is 9984670 square km.",
        )
        self.assertEqual(repr(self.canada), "Country('Canada', 34482779, 9984670)")
        self.assertEqual(str([self.canada]), "[Country('Canada', 34482779, 9984670)]")


class ContinentTests(unittest.TestCase):
    def setUp(self):
        # Khôi phục biến lớp để các bài kiểm thử không ảnh hưởng lẫn nhau.
        self.addCleanup(setattr, Continent, "total_continents",
                        Continent.total_continents)
        self.canada = Country("Canada", 34482779, 9984670)
        self.usa = Country("United States of America", 313914040, 9826675)
        self.mexico = Country("Mexico", 112336538, 1943950)

    def test_sample_totals_and_largest(self):
        north = Continent("North America", [self.canada, self.usa, self.mexico])
        self.assertEqual(north.total_population(), 460733357)
        self.assertEqual(north.total_area(), 21755295)
        self.assertIs(north.get_largest_country(), self.canada)
        self.assertEqual(len(north), 3)
        self.assertEqual(str(north).splitlines(), [
            "North America", str(self.canada), str(self.usa), str(self.mexico)
        ])

    def test_empty_continent(self):
        empty = Continent("Empty")
        self.assertEqual(len(empty), 0)
        self.assertEqual(empty.total_population(), 0)
        self.assertEqual(empty.total_area(), 0)
        self.assertIsNone(empty.get_largest_country())
        self.assertEqual(str(empty), "Empty")

    def test_counter_counts_only_successful_construction(self):
        before = Continent.total_continents
        Continent("North America", [self.canada])
        Continent("Asia")
        self.assertEqual(Continent.total_continents, before + 2)
        with self.assertRaises(TypeError):
            Continent("Invalid", [self.canada, "Japan"])
        self.assertEqual(Continent.total_continents, before + 2)

    def test_add_country_and_reject_wrong_type(self):
        asia = Continent("Asia")
        vietnam = Country("Vietnam", 98000000, 331212)
        asia.add_country(vietnam)
        self.assertEqual(len(asia), 1)
        self.assertIs(asia.countries[0], vietnam)
        with self.assertRaises(TypeError):
            asia.add_country("Japan")
        self.assertEqual(asia.countries, [vietnam])

    def test_lists_are_independent(self):
        first, second = Continent("A"), Continent("B")
        first.add_country(self.canada)
        self.assertEqual(second.countries, [])
        supplied = [self.canada]
        copied = Continent("C", supplied)
        supplied.append(self.usa)
        self.assertEqual(copied.countries, [self.canada])


class NematodeTests(unittest.TestCase):
    def setUp(self):
        self.worm = Nematode(1.05, "hermaphrodite", 3)

    def test_constructor_and_representations(self):
        self.assertEqual(self.worm.get_body_length(), 1.05)
        self.assertEqual(self.worm.get_gender(), "hermaphrodite")
        self.assertEqual(self.worm.get_age(), 3)
        self.assertEqual(str(self.worm),
                         "Nematode(Length: 1.05mm, Gender: hermaphrodite, Age: 3 days)")
        self.assertEqual(repr(self.worm), "Nematode(1.05, 'hermaphrodite', 3)")
        self.assertEqual(Nematode(1, "MALE", 0).get_gender(), "male")

    def test_invalid_constructor_values(self):
        for args in ((-0.5, "male", 1), (0, "male", 1), (1, "female", 2),
                     (1, "male", -1), (1, "male", 1.5), (1, "male", True),
                     (float("nan"), "male", 1), (float("inf"), "male", 1)):
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    Nematode(*args)

    def test_private_name_mangling(self):
        # getattr tránh việc Python đổi tên thuộc tính theo chính lớp test.
        with self.assertRaises(AttributeError):
            getattr(self.worm, "__body_length")
        self.assertEqual(getattr(self.worm, "_Nematode__body_length"), 1.05)

    def test_growth_sample(self):
        self.worm.grow(2, 0.15)
        self.assertEqual(self.worm.get_age(), 5)
        self.assertAlmostEqual(self.worm.get_body_length(), 1.2)
        self.worm.grow(0, 0)
        self.assertEqual(self.worm.get_age(), 5)
        self.assertAlmostEqual(self.worm.get_body_length(), 1.2)

    def test_setters_validate_without_changing_state(self):
        self.worm.set_body_length(1.3)
        self.worm.set_age(4)
        self.worm.set_age(4)
        for age in (3, -1, 4.5, True):
            with self.subTest(age=age):
                with self.assertRaises(ValueError):
                    self.worm.set_age(age)
                self.assertEqual(self.worm.get_age(), 4)
        for length in (0, -1, float("nan"), float("inf")):
            with self.subTest(length=length):
                with self.assertRaises(ValueError):
                    self.worm.set_body_length(length)
                self.assertEqual(self.worm.get_body_length(), 1.3)

    def test_failed_growth_is_atomic(self):
        for days, growth in ((-1, 0.1), (1.5, 0.1), (True, 0.1),
                             (2, -0.1), (2, float("inf")),
                             (2, float("nan")), (2, "0.1"), (2, True)):
            with self.subTest(days=days, growth=growth):
                with self.assertRaises((ValueError, TypeError)):
                    self.worm.grow(days, growth)
                self.assertEqual(self.worm.get_age(), 3)
                self.assertEqual(self.worm.get_body_length(), 1.05)
        large = Nematode(1e308, "male", 0)
        with self.assertRaises(ValueError):
            large.grow(1, 1e308)
        self.assertEqual(large.get_age(), 0)
        self.assertEqual(large.get_body_length(), 1e308)


class AcademicTests(unittest.TestCase):
    def setUp(self):
        self.student = Student("SV01", "An", "an@gdu.edu.vn", "KTPM", 3.65)
        self.faculty = Faculty("GV01", "Quang", "quang@gdu.edu.vn", "CNTT", "Tiến sĩ")
        self.member = Member("MB01", "Hoa", "hoa@gdu.edu.vn")

    def test_super_initializes_base_and_subclass_attributes(self):
        self.assertEqual(self.student.name, "An")
        self.assertEqual(self.student.email, "an@gdu.edu.vn")
        self.assertEqual(self.student.major, "KTPM")
        self.assertEqual(self.student.gpa, 3.65)
        self.assertEqual(self.faculty.name, "Quang")
        self.assertEqual(self.faculty.department, "CNTT")
        self.assertEqual(self.faculty.academic_rank, "Tiến sĩ")
        self.assertEqual(Student("S2", "B", "b@gdu.edu.vn", "CNTT").gpa, 0.0)

    def test_enroll_and_complete_course(self):
        self.student.enroll_course("Python")
        self.student.enroll_course("CSDL")
        self.student.complete_course("Python")
        self.assertEqual(self.student.current_courses, ["CSDL"])
        self.assertEqual(self.student.courses_taken, ["Python"])
        self.student.complete_course("Python")
        self.assertEqual(self.student.courses_taken, ["Python"])

    def test_lists_belong_to_each_instance(self):
        other = Student("S2", "B", "b@gdu.edu.vn", "CNTT")
        self.student.enroll_course("Python")
        self.student.complete_course("Python")
        self.assertEqual(other.current_courses, [])
        self.assertEqual(other.courses_taken, [])
        self.faculty.assign_course("Python")
        other_faculty = Faculty("F2", "C", "c@gdu.edu.vn", "CNTT", "Thạc sĩ")
        self.assertEqual(self.faculty.teaching_courses, ["Python"])
        self.assertEqual(other_faculty.teaching_courses, [])

    def test_polymorphic_roles_and_details(self):
        members = [self.student, self.faculty, self.member]
        self.assertEqual([m.get_role() for m in members],
                         ["Sinh viên Đại học", "Giảng viên Khoa", "Thành viên chung"])
        self.student.enroll_course("Python")
        self.faculty.assign_course("Python")
        self.assertIn("| Ngành: KTPM | GPA: 3.65 | Đang học: 1 môn",
                      self.student.get_details())
        self.assertIn("Tiến sĩ", self.faculty.get_details())
        self.assertIn("CNTT", self.faculty.get_details())
        self.assertIn("Python", self.faculty.get_details())
        self.assertEqual(self.member.get_details(),
                         "Mã: MB01 | Họ tên: Hoa | Email: hoa@gdu.edu.vn")
        for member in members:
            self.assertEqual(str(member), member.get_details())

    def test_inheritance_and_mro(self):
        self.assertIsInstance(self.student, Member)
        self.assertTrue(issubclass(Student, Member))
        self.assertTrue(issubclass(Faculty, Member))
        self.assertEqual([cls.__name__ for cls in Student.mro()],
                         ["Student", "Member", "object"])

    def test_representations_identify_actual_class(self):
        self.assertEqual(repr(self.member), "Member('MB01', 'Hoa', 'hoa@gdu.edu.vn')")
        self.assertEqual(repr(self.student),
                         "Student('SV01', 'An', 'an@gdu.edu.vn', 'KTPM', 3.65)")
        self.assertEqual(repr(self.faculty),
                         "Faculty('GV01', 'Quang', 'quang@gdu.edu.vn', 'CNTT', 'Tiến sĩ')")


if __name__ == "__main__":
    unittest.main(verbosity=2)
