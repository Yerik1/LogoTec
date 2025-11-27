# server_test.py
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("0.0.0.0", 9000))
s.listen(1)
print("Servidor prueba en :9000")
conn, addr = s.accept()
print("Conectado desde", addr)
try:
    while True:
        data = conn.recv(1024)
        if not data:
            break
        for line in data.decode().splitlines():
            print("RECIBIDO:", repr(line))
finally:
    conn.close()
    s.close()