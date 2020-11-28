import socket
import os
import sys
import time
import pickle
import myAppProtocol
import json
import getpass
import threading
import time

TCP_BUFFER = 1024
COMMANDS = {1: "LOGIN", 2: "REGISTER", 3: "CREATECLASS", 4: "POST", 5: "JOIN CLASS"}

MY_IP = socket.gethostname()
SERVER_IP = socket.gethostname()

username = None
password = None

def getConnectiontoServer():
    Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip = socket.gethostbyname(socket.gethostname())
    Socket.connect((SERVER_IP, 12345))
    return Socket


sessionUsersList = None
exitSession_var = 1
def updateSessionListThread():
    global sessionUsersList
    global exitSession_var

    while True:
        request = myAppProtocol.Request("GET SESSION USERS")
        request.setuserdetails(username, password)
        Socket = getConnectiontoServer()
        myAppProtocol.sendAppProtocolPacket(Socket, request)
        responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
        Socket.close()
        responseMsg = json.loads(responseMsg)
        if(responseMsg["error"]==0):
            temp_list = list(map(lambda x: x.split(','), responseMsg["message"].strip("[]").split("], [")))
            temp_list2 = list()
            for i in temp_list:
                temp = list()
                temp.append(i[0].strip(' "'))
                temp.append(i[1].strip(' "'))
                temp.append(i[2].strip(' "'))
                temp_list2.append(temp)
            sessionUsersList = temp_list2[:]

        time.sleep(2.0)
        if(exitSession_var==1):
            print("Stopping Session List Thread")
            break
    

def chatsSessionThread(clientSocket):
    global sessionUsersList
    global exitSession_var
    clientSocket.settimeout(2.0)
    while True:
        try:
            msg, address = clientSocket.recvfrom(1024)
            msg = msg.decode("utf-8")
            for i in sessionUsersList:
                if(i[1]==address[0] and int(i[2])==address[1]):
                    print(i[0] + ": " + msg)
                    break
        except socket.timeout:
            if(exitSession_var==1):
                print("Stopping Chat List Thread")
                return


def exitSession(ip,port):
    request = myAppProtocol.Request("EXIT SESSION")
    request.setuserdetails(username, password)
    request.setsessiondetails(ip,port)
    Socket = getConnectiontoServer()
    myAppProtocol.sendAppProtocolPacket(Socket, request)
    responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
    Socket.close()
    responseMsg = json.loads(responseMsg)
    return responseMsg


def broadcastComment(socket, cmt):
    global sessionUsersList
    global exitSession_var
    
    for i in sessionUsersList:
        # print(i[0], i[1], i[2])
        socket.sendto(bytes(cmt, "utf-8"), (i[1],int(i[2])))


def sessionMode(ip, port):
    global sessionUsersList
    global exitSession_var

    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    clientSocket.bind((ip, int(port)))
    
    exitSession_var = 0

    sessionListThread = threading.Thread(target=updateSessionListThread)
    chatsThread = threading.Thread(target=chatsSessionThread, args=(clientSocket,))

    sessionListThread.start()
    chatsThread.start()

    while True:
        print("1 Post Comment\n2 Exit Session")
        cmd = int(input())
        if(cmd==1):
            print("Comment Content: ")
            cmt = input()
            broadcastComment(clientSocket, cmt)
        elif(cmd==2):
            exitSession_var = 1
            sessionListThread.join()
            chatsThread.join()
            clientSocket.close()
            break
    
    return exitSession(ip, port)
            



    

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
            request.setpostparams(postkeyword, postcontent)      
        elif cmd=="JOIN CLASS":
            print("Class Code")
            classid = int(input())
            request.setjoinclassparams(classid)
        elif cmd == "GET POST BY KEYWORD":
            print("Post Keyword:")
            postkeyword = input()
            request.setpostparams(postkeyword,"")
        elif cmd=="NEW DISCUSSION":
            print("Discussion Topic: ")
            topic = input()
            request.setnewdiscussionparams(topic)
        elif cmd=="GET DISCUSSION COMMENTS":
            print("Discussion ID: ")
            discussion_id = int(input())
            request.setgetcommentsparams(discussion_id)
        elif cmd=="POST DISCUSSION COMMENT":
            print("Discussion ID: ")
            discussion_id = int(input())
            print("Comment Type (1: PUBLIC 2:PRIVATE(Visible only to instructor)):")
            temp = int(input()) - 1
            l = ['PUBLIC', 'PRIVATE']
            comment_type = l[temp]
            print("Comment Comtent: ")
            comment = input()
            request.setnewcommentparams(discussion_id, comment_type, comment)
        elif cmd=="START SESSION" or cmd=="JOIN SESSION":
            request.setsessiondetails(MY_IP, '8888')
            Socket = getConnectiontoServer()
            myAppProtocol.sendAppProtocolPacket(Socket, request)
            responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
            Socket.close()
            responseMsg = json.loads(responseMsg)
            if(responseMsg["error"]==0):
                responseMsg = sessionMode(MY_IP, '8888')
            print(responseMsg["message"])
            continue
        
    Socket = getConnectiontoServer()
    myAppProtocol.sendAppProtocolPacket(Socket, request)
    responseMsg = myAppProtocol.receiveAppProtocolPacket(Socket,TCP_BUFFER)
    Socket.close()
    responseMsg = json.loads(responseMsg)
    print(responseMsg["message"])