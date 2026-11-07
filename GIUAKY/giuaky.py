import copy 
list_a = [10, [20, 30], {'a': 1}] 
list_b = list_a 
list_c = copy.copy(list_a) 
list_b[0] = 99 
list_c[1].append(40) 
list_c[2]['b'] = 2 
print("1. list_a[0] =", list_a[0]) 
print("2. list_a[1] =", list_a[1]) 
print("3. list_a[2] =", list_a[2]) 
print("4. list_b is list_a:", list_b is list_a) 
print("5. list_c is list_a:", list_c is list_a) 
