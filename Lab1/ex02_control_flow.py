# ex02_control_flow.py
# 1. Toán tử đặc trưng
print("17 // 3 =", 17 // 3) # Chia lấy phần nguyên: 5
print("17 % 3 =", 17 % 3) # Chia lấy phần dư: 2
print("2 ** 8 =", 2 ** 8) # Lũy thừa: 256
# 2. Cấu trúc if-elif-else
score = float(input("Nhập điểm: "))
if score >= 90:
	grade = "A (Xuất sắc)"
elif score >= 75:
	grade = "B (Khá / Giỏi)"
elif score >= 60:
	grade = "C (Trung bình)"
elif score >= 50:
	grade = "D (Trung bình yếu)"
else:
	grade = "F (Không đạt)"
print(f"Điểm: {score} -> Xếp loại: {grade}")
# 3. Vòng lặp kết hợp break và continue
print("--- Vòng lặp với continue và break ---")
for n in range(10):
	if n % 2 == 0:
		continue # Bỏ qua số chẵn
	if n == 7:
		print("Gặp số 7 -> Dừng vòng lặp (break)")
		break
	print(f"Số lẻ: {n}")