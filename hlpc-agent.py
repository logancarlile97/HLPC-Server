""" # Logan Carlile
# HLPC-Agent
# 11/14/2021

import socket

HEADER = 64
PORT = 5540
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    print(client.recv(2048).decode(FORMAT))


input()
for _ in range(1000000):
    send("Hey there")
send("!DISCONNECT")
 """

import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
for p in ports:
    print(p)