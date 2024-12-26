n = int(input())
mas = []
flag = True
for i in range(n):
    try:
        mas.append(int(input()))
        flag = False
    except ValueError:
        print("No")
if flag:
    print(max(mas))