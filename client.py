import socket
import os
import sys
import time
import pickle
import myAppProtocol
import json
import getpass

TCP_BUFFER = 1024
COMMANDS = {1: "LOGIN", 2: "REGISTER", 3: "CREATECLASS", 4: "POST", 5: "JOIN CLASS"}


def getConnectiontoServer():
    Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Socket.connect(('', 12345))
    Socket.connect((socket.gethostname(), 12345))
    return Socket
    

username = None
password = None


request = myAppProtocol.Request("GETLOGINPAGE")
Socket = getConnectiontoServer()
myAppProtocol.sendAppProtocolPacket(Socket, request)
responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
Socket.close()

responseMsg = json.loads(responseMsg)
if(responseMsg["error"]==1):
    print("Unexpected server Error")
    exit(1)
print(responseMsg["message"])

while True:
    c = 1
    for i in responseMsg["cmd_list"]:
        if type(i) is list:
            print(c,*i)
        else:
            print(c,i)
        c+=1
    temp = int(input())
    if(not 1<=temp<c):
        print("Wrong Command Number")
        continue
    cmd = responseMsg["cmd_list"][temp-1]

    request = myAppProtocol.Request(cmd)

    if cmd=="LOGIN":
        print("Username: ")
        username = input()
        # print("password")
        # password = input()
        password = getpass.getpass()
        request.setuserdetails(username, password)
    
    elif cmd=="REGISTER":
        print("Username: ")
        username = input()
        # print("password")
        # password = input()
        password = getpass.getpass()
        request.setuserdetails(username, password)
        print("Usertype (1:Instructor 2:Student)")
        ut = int(input())
        if(ut==1):
            request.setregisterparams("INSTRUCTOR")
        elif(ut==2):
            request.setregisterparams("STUDENT")
    
    else:
        request.setuserdetails(username, password)
        if cmd=="CREATE CLASS":
            print("Classname")
            classname = input()
            request.setnewclassparams(classname)
        
        elif cmd=="NEW POST":
            print("Post Keyword:")
            postkeyword = input()
            print("Post Content:")
            postcontent = input()
<<<<<<< Updated upstream
            request.setpostparams(postkeyword, postcontent)      
=======
            request.setpostparams(postkeyword, postcontent)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        elif cmd=="JOIN CLASS":
            print("Class Code")
            classid = int(input())
            request.setjoinclassparams(classid)
        elif cmd == "GET POST BY KEYWORD":
            print("Post Keyword:")
            postkeyword = input()
            request.setpostparams(postkeyword,"")
        
    Socket = getConnectiontoServer()
    myAppProtocol.sendAppProtocolPacket(Socket, request)
    responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
    Socket.close()
    responseMsg = json.loads(responseMsg)
    print(responseMsg["message"])