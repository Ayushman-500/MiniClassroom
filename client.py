import socket
import os
import sys
import time
import pickle
import myAppProtocol
import json

TCP_BUFFER = 1024
COMMANDS = {1: "LOGIN", 2: "REGISTER", 3: "CREATECLASS", 4: "POST", 5: "JOINCLASS"}


def getConnectiontoServer():
    Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    Socket.connect(('', 12345))
    return Socket
    

username = None
password = None

responseMsg = None

while True:
    print("1 Login \n2 Register")
    cmd = int(input())
    if(cmd==1):
        print("Username:")
        username = input()
        print("password")
        password = input()
        request = myAppProtocol.Request("LOGIN", username, password)
        
        Socket = getConnectiontoServer()
        myAppProtocol.sendAppProtocolPacket(Socket, request)
        responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
        Socket.close()

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
        
        Socket = getConnectiontoServer()
        myAppProtocol.sendAppProtocolPacket(Socket, request)
        responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
        Socket.close()
    
    print(responseMsg)
    responseMsg = json.loads(responseMsg)
    print(responseMsg["message"])
    if(responseMsg["error"]==0):
        break



while True:
    c = 1
    for i in responseMsg["cmd_list"]:
        print(c,i)
        c+=1
    cmd = int(input())
    request = myAppProtocol.Request(cmd, username, password)
    Socket = getConnectiontoServer()
    myAppProtocol.sendAppProtocolPacket(Socket, request)
    responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
    Socket.close()
    responseMsg = json.loads(responseMsg)
    print(responseMsg["message"])