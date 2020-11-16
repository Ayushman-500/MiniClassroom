import socket
import os
import sys
import time
import pickle
import myAppProtocol

TCP_BUFFER = 1024
COMMANDS = {1: "LOGIN", 2: "REGISTER", 3: "CREATECLASS", 4: "POST", 5: "JOINCLASS"}

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect(('', 12345))

username = None
password = None

print("1.Login \n2.Register")
cmd = int(input())
if(cmd==1):
    print("Username:")
    username = input()
    print("password")
    password = input()
    request = myAppProtocol.Request("LOGIN", username, password)
    
    myAppProtocol.sendAppProtocolPacket(socket, request)
    responseMsg = myAppProtocol.receiveAppProtocolPacket(socket,TCP_BUFFER)
    print(responseMsg)

elif(cmd==2):
    print("Username:")
    username = input()
    print("Password")
    password = input()
    print("Usertype (1:Instructor 2:Student)")
    ut = int(input())
    request = myAppProtocol.Request("REGISTER", username, password)
    if(ut==1):
        request.setregisterparams("INSTRUCTOR")
    elif(ut==2):
        request.setregisterparams("STUDENT")
    
    myAppProtocol.sendAppProtocolPacket(socket, request)
    responseMsg = myAppProtocol.receiveAppProtocolPacket(socket,TCP_BUFFER)
    print(responseMsg)