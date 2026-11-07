# ex03_comprehensions.py
# 1. List Comprehension
squares = [x * x for x in range(10)]
print("Danh sách bình phương (0-9):", squares)
temps_c = [20, 25, 30, 35, 40]
temps_f = [c * 1.8 + 32 for c in temps_c]
print("Nhiệt độ độ F:", temps_f)
words = ["python", "code", "ai", "developer", "gdu", "data"]
long_words = [w.upper() for w in words if len(w) > 4]
print("Các từ dài > 4 ký tự in hoa:", long_words)
# 2. Dictionary Comprehension
square_dict = {x: x**2 for x in range(1, 6)}
print("Dict bình phương:", square_dict)
names = ["An", "Binh", "Chi", "Dung"]
grades = [8.5, 7.0, 9.0, 6.5]
student_grades = {name: score for name, score in zip(names, grades)}
print("Dict sinh viên - điểm:", student_grades)
# 3. Set Comprehension

nums = [1, 2, 3, 4, 5, 6, 7, 8, 9]
unique_remainders = {x % 3 for x in nums}
print("Set các số dư khi chia cho 3:", unique_remainders)
sample_text = "truong dai hoc gia dinh"
vowels = {char for char in sample_text if char in "aeiou"}
print("Tập hợp nguyên âm trong chuỗi:", vowels)
