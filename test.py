import time

time_now = time.time()
time_later = time_now + 120
# print(time_now + " " + time_later)

a = b'abcd\r\nbcde'
b = a.split(b"\r\n")
print(b)

with open("./wb.txt", 'wb') as fw:
    fw.write(b"abcd")

