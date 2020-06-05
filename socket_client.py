import socket
from time import sleep
HOST = 'localhost'
PORT = 5000
'''
TEMP STATUS:
    0: Unknown
     1: Stable
     2: Tracking
     5: Near
     6: Chasing
     7: Filling/emptying reservoir
     10: Standby
     15: General failure in temp control
 '''
with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    s.connect((HOST,PORT))
    s.sendall(b'TEMP?')
    data = s.recv(1024)
    print('Recived: ', data.decode())

    s.sendall(b'CHAMBER?')
    data = s.recv(1024)
    print('Recived: ', data.decode())

    s.sendall(b'TIME?')
    data = s.recv(1024)
    print('Recived: ', data.decode())

    s.sendall(b'RANGE?')
    data = s.recv(1024)
    print('Recived: ', data.decode())

    s.sendall(b'FIELD?')
    data = s.recv(1024)
    print('Recived: ', data.decode())
    
    setpoint = 2000
    rate =100
    mode = 2

    s.sendall(bytes("FIELD {0},{1},{2},1".format(setpoint,rate,mode),'utf-8'))
    data = s.recv(1024)
    print('Recived: ', data.decode())

    s.sendall(b'FIELD?')
    data = s.recv(1024)
    print('Recived: ', data.decode())

    s.send(b'exit')
