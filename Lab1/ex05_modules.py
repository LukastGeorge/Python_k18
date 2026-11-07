# math_utils.py
import math
def is_prime(n):
	"""Kiểm tra số nguyên tố."""
	if n < 2:
		return False
	for i in range(2, int(math.isqrt(n)) + 1):
		if n % i == 0:
			return False
	return True


def factorial(n):
	"""Tính giai thừa n!"""
	if n < 0:
		raise ValueError("Không tính giai thừa số âm")
	result = 1
	for i in range(2, n + 1):
		result *= i
	return result


def gcd(a, b):
	"""Tìm ước chung lớn nhất."""
	return math.gcd(a, b)

# ex05_modules.py
import ex05_modules
import random
from math import sqrt, pi
def main():
	print("=== SỬ DỤNG MODULE THƯ VIỆN CHUẨN ===")
	print(f"Căn bậc hai của 49: {sqrt(49)}")
	print(f"Hằng số Pi: {pi:.4f}")
	print(f"Số ngẫu nhiên từ 1 đến 100: {random.randint(1, 100)}")
	print("=== SỬ DỤNG CUSTOM MODULE math_utils ===")
	test_num = 29
	print(f"{test_num} có phải số nguyên tố? -> {ex05_modules.is_prime(test_num)}")
	print(f"5! = {ex05_modules.factorial(5)}")
	print(f"Ước chung lớn nhất của 48 và 60: {ex05_modules.gcd(48, 60)}")
if __name__ == "__main__":
	main()