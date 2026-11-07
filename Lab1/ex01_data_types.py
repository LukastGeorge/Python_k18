# ex01_data_types.py
# 1. Các kiểu dữ liệu cơ bản

age = 20  #int 
gpa = 3.75 #float

full_name = "Le Van B" # str
is_active = True # bool
address = None # NoneType
print(f"age: {age} ({type(age)})")
print(f"gpa: {gpa} ({type(gpa)})")
print(f"full_name: {full_name} ({type(full_name)})")
print(f"is_active: {is_active} ({type(is_active)})")
print(f"address: {address} ({type(address)})")

# 2. Các kiểu tập hợp (Collections)
scores = [8.5, 7.0, 9.0, 7.0]
coords = (10.75, 106.66)
unique_tags = {"python", "ai", "web", "python"}
student = {"id": "2211002", "name": "Le Van B", "major": "Software Engineering"}
print("\n--- Collections ---")
print("List:", scores)
print("Tuple:", coords)
print("Set (loại bỏ trùng):", unique_tags)
print("Dict:", student)

# 3. Ép kiểu
num_int = int("125")
num_float = float("3.1415")
num_str = str(100)
char_list = list("GDU")
bool_val_0 = bool(0)
bool_val_1 = bool(1)

print("\n--- Type Conversion ---")
print("int('125') ->", num_int)
print("float('3.1415') ->", num_float)
print("str(100)->", num_str)
print("list('GDU') ->", char_list)
print("bool(0) ->", bool_val_0)
print("bool(1) ->", bool_val_1)
