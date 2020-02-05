import socket
from time import sleep
HOST = 'localhost'
PORT = 5000



s =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((HOST,PORT))
s.listen()
print('listening at {}, port: {}'.format(HOST,PORT))
RUN = True
while RUN:
    conn, addr = s.accept()
    while True:
        data = conn.recv(1024)
        #if not data: break
        if data == b'exit':
            print('exiting')
            RUN = False
            break
        if data == b'disconnect':
            break
        print('Connected by ', addr)
        print(data)
        conn.sendall(b"data revieved.\n")
    conn.close()
    print('client disconnected')
    sleep(1)
