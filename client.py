import socket
import os
import sys
import time
import pickle
import myAppProtocol
import utils

TCP_BUFFER = 1024
COMMANDS = {1: "LOGIN", 2: "REGISTER", 3: "CREATECLASS", 4: "POST", 5: "JOINCLASS"}

clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.connect(('', 12345))

username = None
password = None

print("1.Login \n 2.Register")
cmd = int(input())
if(cmd==1):
    print("Username:")
    username = input()
    print("password")
    password = input()
    request = myAppProtocol.Request("LOGIN", username, password)
    msg = pickle.dumps(request)
    clientSocket.sendall(msg)
    msg = utils.receivePacket(clientSocket, TCP_BUFFER)
    print(msg.decode('utf-8'))
elif(cmd==2):
    print("Username:")
    username = input()
    print("Password")
    password = input()
    print("Usertype (1:Instructor 2:Student)")
    ut = int(input())
    request = myAppProtocol.Request("LOGIN", username, password)
    if(ut==1):
        request.setregisterparams("INSTRUCTOR")
    elif(ut==2):
        request.setregisterparams("STUDENT")
    msg = pickle.dumps(request)
    clientSocket.sendall(msg)
    msg = utils.receivePacket(clientSocket, TCP_BUFFER)
    print(msg.decode('utf-8'))