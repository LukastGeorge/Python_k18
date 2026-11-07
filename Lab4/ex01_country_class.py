"""Bài 3.1: Lớp Country, constructor, self, __str__ và __repr__."""

import math


class Country:
    """Biểu diễn một quốc gia với dân số và diện tích theo km²."""

    def __init__(self, name, population, area):
        """Khởi tạo quốc gia có dân số không âm và diện tích dương."""
        if not isinstance(name, str):
            raise TypeError("Tên quốc gia phải là chuỗi!")
        if not isinstance(population, int) or isinstance(population, bool):
            raise TypeError("Dân số phải là số nguyên!")
        if not isinstance(area, (int, float)) or isinstance(area, bool):
            raise TypeError("Diện tích phải là số!")
        if population < 0:
            raise ValueError("Dân số không được âm!")
        if area <= 0 or not math.isfinite(area):
            raise ValueError("Diện tích phải là số dương hữu hạn!")

        # self là đối tượng đang được khởi tạo; mỗi quốc gia có dữ liệu riêng.
        self.name = name
        self.population = population
        self.area = area

    def is_larger(self, other):
        """So sánh diện tích với một đối tượng Country khác."""
        if not isinstance(other, Country):
            raise TypeError("Đối tượng so sánh phải thuộc lớp Country!")
        return self.area > other.area

    def population_density(self):
        """Trả về mật độ dân số, đơn vị người/km²."""
        return self.population / self.area

    def __str__(self):
        """Chuỗi thân thiện được dùng khi gọi print(country)."""
        return (
            f"{self.name} has a population of {self.population} "
            f"and is {self.area} square km."
        )

    def __repr__(self):
        """Chuỗi mô tả cách khởi tạo đối tượng, phục vụ gỡ lỗi."""
        # !r dùng repr của tên để xử lý đúng cả tên chứa dấu nháy.
        return f"Country({self.name!r}, {self.population!r}, {self.area!r})"


def main():
    """Minh họa các nhiệm vụ và trường hợp dữ liệu sai của bài 3.1."""
    canada = Country("Canada", 34482779, 9984670)
    usa = Country("United States of America", 313914040, 9826675)
    vietnam = Country("Vietnam", 98000000, 331212)

    print("1. Khởi tạo đối tượng và biểu diễn bằng __str__")
    print(canada)
    print(usa)

    print("\n2. Mật độ dân số và so sánh diện tích")
    print("Mật độ Canada:", canada.population_density(), "người/km²")
    print("Mật độ Vietnam:", vietnam.population_density(), "người/km²")
    print("Canada lớn hơn USA:", canada.is_larger(usa))
    print("Vietnam lớn hơn Canada:", vietnam.is_larger(canada))

    print("\n3. Danh sách đối tượng và __repr__")
    countries = [canada, usa, vietnam]
    print(countries)
    print(
        "List biểu diễn từng phần tử bằng repr(), nên Python gọi __repr__. "
        "In một quốc gia trực tiếp bằng print() sẽ gọi __str__."
    )

    print("\n4. Bắt lỗi dữ liệu không hợp lệ")
    for name, population, area in (
        ("ErrorLand", -100, 500),
        ("X", 100, -10),
        ("ZeroArea", 100, 0),
    ):
        try:
            Country(name, population, area)
        except ValueError as error:
            print(f"ValueError: {error}")

    try:
        canada.is_larger("USA")
    except TypeError as error:
        print(f"TypeError: {error}")


if __name__ == "__main__":
    main()
