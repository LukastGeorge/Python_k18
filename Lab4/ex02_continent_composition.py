"""Bài 3.2: Quan hệ chứa giữa lớp Continent và các đối tượng Country."""

from ex01_country_class import Country


class Continent:
    """Lưu các quốc gia thuộc một châu lục và tổng hợp thông tin của chúng."""

    total_continents = 0

    def __init__(self, name, countries=None):
        """Tạo châu lục với bản sao riêng của danh sách các quốc gia."""
        country_list = [] if countries is None else list(countries)
        for country in country_list:
            if not isinstance(country, Country):
                raise TypeError("Phải thêm một đối tượng thuộc lớp Country!")

        self.name = name
        self.countries = country_list
        Continent.total_continents += 1

    def add_country(self, country):
        """Thêm một quốc gia sau khi kiểm tra đúng kiểu Country."""
        if not isinstance(country, Country):
            raise TypeError("Phải thêm một đối tượng thuộc lớp Country!")
        self.countries.append(country)

    def total_population(self):
        """Trả về tổng dân số; châu lục chưa có quốc gia trả về 0."""
        return sum(country.population for country in self.countries)

    def total_area(self):
        """Trả về tổng diện tích các quốc gia, tính bằng km²."""
        return sum(country.area for country in self.countries)

    def get_largest_country(self):
        """Trả về quốc gia có diện tích lớn nhất hoặc None nếu rỗng."""
        return max(
            self.countries, key=lambda country: country.area, default=None
        )

    def __len__(self):
        """Cho phép dùng len(continent) để đếm số quốc gia."""
        return len(self.countries)

    def __str__(self):
        """Hiển thị tên châu lục rồi mỗi quốc gia trên một dòng."""
        lines = [self.name]
        lines.extend(str(country) for country in self.countries)
        return "\n".join(lines)

    def __repr__(self):
        """Biểu diễn tên và danh sách quốc gia khi kiểm tra đối tượng."""
        return f"Continent({self.name!r}, {self.countries!r})"


def main():
    """Minh họa quan hệ chứa, biến lớp và kiểm tra kiểu khi thêm quốc gia."""
    canada = Country("Canada", 34482779, 9984670)
    usa = Country("United States of America", 313914040, 9826675)
    mexico = Country("Mexico", 112336538, 1943950)
    vietnam = Country("Vietnam", 98000000, 331212)

    north_america = Continent("North America", [canada, usa, mexico])
    asia = Continent("Asia")
    asia.add_country(vietnam)

    print("=== CHÂU LỤC VÀ QUỐC GIA ===")
    print(north_america)
    print(f"Số quốc gia: {len(north_america)}")
    print(f"Tổng dân số: {north_america.total_population()}")
    print(f"Tổng diện tích: {north_america.total_area()} km²")
    print(f"Quốc gia lớn nhất: {north_america.get_largest_country().name}")
    print()
    print(asia)
    print(f"Số quốc gia ở Asia: {len(asia)}")
    print(f"Số châu lục đã tạo: {Continent.total_continents}")

    try:
        asia.add_country("Japan")
    except TypeError as error:
        print(f"Không thể thêm quốc gia: {error}")


if __name__ == "__main__":
    main()
