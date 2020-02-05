import socket
from time import sleep
import qdcommandparser
HOST = 'localhost'
PORT = 5000

dyna = qdcommandparser.QDCommandParser('DYNACOOL')
s =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.bind((HOST,PORT))
s.listen()
s.settimeout(2.0)
print('listening at {}, port: {}'.format(HOST,PORT))
RUN = True
while RUN:
    try:
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
            print('Connected by: ', addr)
            print('command:',data)
            answer = dyna.parse_cmd(data)
            conn.sendall(bytes(answer,'utf-8'))
        conn.close()
        print('client disconnected')
        sleep(0.5)
    except socket.timeout:
        pass
