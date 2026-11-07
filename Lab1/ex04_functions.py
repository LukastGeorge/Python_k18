# ex04_functions.py
# 1. Hàm có tham số mặc định
def calculate_total(price, quantity, discount=0.0):
 """Tính tổng tiền thanh toán sau giảm giá."""
 return price * quantity * (1.0 - discount)
print("Đơn hàng 1 (không giảm giá):", calculate_total(50000, 3))
print("Đơn hàng 2 (giảm giá 10%):", calculate_total(100000, 2, discount=0.1))
# 2. Tầm vực biến Local vs Global
counter = 0 # Biến toàn cục
def increment():
 global counter
 counter += 1
 local_msg = f"Counter hiện tại: {counter}" # Biến cục bộ
 print(local_msg)
increment()
increment()

# 3. Hàm Lambda
cube = lambda x: x ** 3
print("Lambda 7 ** 3 =", cube(7))
# Sắp xếp danh sách sinh viên theo điểm giảm dần với lambda
students = [("Nguyen An", 8.5), ("Tran Binh", 9.2), ("Le Chi", 7.8)]
sorted_students = sorted(students, key=lambda student: student[1], reverse=True)
print("Danh sách sau sắp xếp theo điểm:", sorted_students)