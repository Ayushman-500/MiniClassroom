# Libraries
import socket
import sys
import os
import threading
import time
import json
import myAppProtocol
import sqlite3
import datetime

# Constants
TCP_BUFFER = 1024
MAX_TCP_PAYLOAD = 1024
DEFAULT_PORT = 12345

LOCS = ["LOGINPAGE", "HOME_INSTRUCTOR", "HOME_STUDENT", "MYCLASSES", "INSIDECLASS_INSTRUCTOR", "INSIDECLASS_STUDENT"]

LOC_CMD_MAP = {"LOGINPAGE":["LOGIN", "REGISTER"],
            "HOME_INSTRUCTOR":["CREATE CLASS", "MY CLASSES", "LOGOUT"],
            "MYCLASSES":["HOME"],
            "INSIDECLASS_INSTRUCTOR":["HOME","NEW POST","GET ALL POSTS","GET POST BY KEYWORD", "LOGOUT"],
            "HOME_STUDENT":["JOIN CLASS", "MY CLASSES", "LOGOUT"],
            "INSIDECLASS_STUDENT":["HOME","GET ALL POSTS", "GET POSTS BY KEYWORD", "LOGOUT"]}

lock = threading.Lock()

# Database Connections
def getconnectiontodb():
    conn = sqlite3.connect("./sqlitedb.db")
    cursor = conn.cursor()
    return conn, cursor


# Client States
def createNewClientState(loc, cmd_list, class_id):
    client_state = {"loc":loc, "cmd_list":cmd_list, "class_id":class_id}
    return client_state

def saveClientState(username, client_state):
    client_state = json.dumps(client_state)
    conn, c = getconnectiontodb()
    c.execute("SELECT usertype FROM users WHERE username=?", (username,))
    rows = c.fetchall()
    usertype = rows[0][0]
    try:
        lock.acquire()
        c.execute("DELETE FROM onlineUsers WHERE username=?", (username,))
        c.execute("INSERT INTO onlineUsers (username, usertype, clientstate) VALUES (?, ?, ?)", (username, usertype, client_state))
        conn.commit()
    finally:
        lock.release()

def getClientState(username):
    conn, c = getconnectiontodb()
    c.execute("SELECT * FROM onlineUsers WHERE username=?", (username,))
    rows = c.fetchall()
    usertype = rows[0][1]
    client_state = json.loads(rows[0][2])
    return usertype, client_state

def removeClientState(username):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        c.execute("DELETE FROM onlineUsers WHERE username=?", (username,))
        conn.commit()
    finally:
        lock.release()

def isClientStatePresent(username):
    conn, c = getconnectiontodb()
    c.execute("SELECT * FROM onlineUsers WHERE username=?", (username,))
    rows = c.fetchall()
    if(len(rows)!=0):
        return 1
    return 0



# Features of MiniClass

# Authentication, login and registration
def authenticate(username, password):
    conn, c = getconnectiontodb()
    
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    rows = c.fetchall()

    if(len(rows)==0 or rows[0][0]!=password):
        return 0
    
    return 1

def login(username, password):
    conn, c = getconnectiontodb()
    
    c.execute("SELECT password,usertype FROM users WHERE username=?", (username,))
    rows = c.fetchall()

    if(len(rows)==0 or rows[0][0]!=password):
        return 0

    # Save client state
    clientstate = None
    if(rows[0][1]=="INSTRUCTOR"):
        clientstate = createNewClientState("HOME_INSTRUCTOR", LOC_CMD_MAP["HOME_INSTRUCTOR"], -1)
    else:
        clientstate = createNewClientState("HOME_STUDENT", LOC_CMD_MAP["HOME_STUDENT"], -1)
    saveClientState(username, clientstate)
    
    return 1

def register(username, password, usertype):
    conn, c = getconnectiontodb()

    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS users (username text NOT NULL UNIQUE, password text, usertype text NOT NULL);")
    finally:
        lock.release()
    
    # check if same username already exists
    query = f"SELECT * FROM users WHERE username LIKE '{username}'"
    c.execute(query)
    rows = c.fetchall()
    if(len(rows)>0):
        return 2
    
    try:
        lock.acquire()
        # insert new user into database
        c.execute("INSERT INTO users (username, password, usertype) VALUES (?, ?, ?)", (username, password, usertype))
        conn.commit()
    finally:
        lock.release()

    # Save client state
    clientstate = None
    if(usertype=="INSTRUCTOR"):
        clientstate = createNewClientState("HOME_INSTRUCTOR", LOC_CMD_MAP["HOME_INSTRUCTOR"], -1)
    else:
        clientstate = createNewClientState("HOME_STUDENT", LOC_CMD_MAP["HOME_STUDENT"], -1)
    saveClientState(username, clientstate)
    
    conn.commit()
    
    return 1


def getUserType(username):
    conn, c = getconnectiontodb()
    
    c.execute("SELECT usertype FROM users WHERE username=?", (username,))
    rows = c.fetchall()

    return rows[0][0]


# Get, Create classes
def createclass(classname):
    # Create new class
    # Save client state
    return 1

def getClass(classid):
    # Save client state with
    return 1

def getClassId(classname):
    class_id = None #replace None with class_id from classes database
    return class_id

def getpost(class_id,username):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS posts"+ str(class_id)+" (id int(100) NOT NULL AUTO_INCREMENT, classId int(100) NOT NULL,username text NOT NULL,keyword VARCHAR(250) NOT NULL,Content text NOT NULL,timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,);")
    finally:
        lock.release()
    query = f"SELECT * FROM posts"+ str(class_id)+ " ORDER BY timestamp;"
    c.execute(query)
    rows = c.fetchall()
    json_output = json.dumps(rows)
    return(json_output)

    
# Get Create Posts
def createpost(class_id,username,keyword,Content):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS posts"+ str(class_id)+" (id int(100) NOT NULL AUTO_INCREMENT, classId int(100) NOT NULL,username text NOT NULL,keyword VARCHAR(250) NOT NULL,Content text NOT NULL,timestamp timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,);")
    finally:
        lock.release()
<<<<<<< Updated upstream
=======

    # From here we will go to my classes and thus save the state accordingly
    usertype = getUserType(username)
    myClasses(username, usertype)

    # checking if the student is already enrolled in this class
    usertype, clientState = getClientState(username)
    for pos in range(1,len(list(clientState["cmd_list"]))):
        if clientState["cmd_list"][pos][1]==classroomId:
            return 3
    return 1
def getpost(class_id,username):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS posts"+ str(class_id)+" (id INTEGER PRIMARY KEY AUTOINCREMENT, classId INTEGER NOT NULL,username text NOT NULL,keyword text NOT NULL,Content text NOT NULL,date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);")
    finally:
        lock.release()
    query = f"SELECT * FROM posts"+ str(class_id)+ " ORDER BY timestamp DESC;"
    c.execute(query)
    rows = c.fetchall()
    json_output = json.dumps(rows)
    return(json_output)

def createpost(class_id,username,keyword,Content):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS posts"+ str(class_id)+" (id INTEGER PRIMARY KEY AUTOINCREMENT, classId INTEGER NOT NULL,username text NOT NULL,keyword text NOT NULL,Content text NOT NULL,date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);")
    finally:
        lock.release()
    try:
        lock.acquire()
        # insert new post into database
        c.execute("INSERT INTO posts"+ str(class_id)+" (id, classId,username,keyword,Content,timestamp) VALUES (NULL,?, ?,?,?,?)", (class_id,username, keyword, Content,datetime.datetime.now()))
        conn.commit()
    finally:
        lock.release()

    # Save client state
    clientstate = None
    clientstate = createNewClientState(LOCS[3], LOC_CMD_MAP[LOCS[3]], class_id)
    saveClientState(username, clientstate)
    conn.commit()
    return 1
def getpostbykeyword(class_id,username,keyword):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS posts"+ str(class_id)+" (id INTEGER PRIMARY KEY AUTOINCREMENT, classId INTEGER NOT NULL,username text NOT NULL,keyword text NOT NULL,Content text NOT NULL,date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);")
    finally:
        lock.release()
    query = f"SELECT * FROM posts"+ str(class_id)+ " WHERE keyword LIKE '" + str(keyword) + "' ORDER BY timestamp DESC;"
    c.execute(query)
    rows = c.fetchall()
    json_output = json.dumps(rows)
    return(json_output)


def myClasses(username, usertype):
    conn, c = getconnectiontodb()
>>>>>>> Stashed changes
    try:
        lock.acquire()
        # insert new post into database
        c.execute("INSERT INTO posts"+ str(class_id)+" (id, classId,username,keyword,Content,timestamp) VALUES (NULL,?, ?,?,?,NULL)", (class_id,username, keyword, Content))
        conn.commit()
    finally:
        lock.release()

    # Save client state
    clientstate = None
    clientstate = createNewClientState(LOCS[3], LOC_CMD_MAP[LOCS[3]], class_id)
    saveClientState(username, clientstate)
    
    conn.commit()
    
    return 1

<<<<<<< Updated upstream
    # Create new post with class_id from clientstate in onlineUsers db
    # Save client state with LOCS[3]
=======
def getClassname(classroomId):
    conn, c = getconnectiontodb()
    c.execute("SELECT classname FROM classrooms WHERE classroomId =?", (classroomId,))
    classname = c.fetchall()[0]
    return classname

# def getClassId(classname):
#     class_id = None #replace None with class_id from classrooms database
#     return class_id


# Get Create Posts

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
# ...
# other funcs


def handleClient(clientSocket, address):
    try:
        msg = myAppProtocol.receiveAppProtocolPacket(clientSocket, TCP_BUFFER)
        RequestObj = json.loads(msg)
        print(f"Received from {address}: {RequestObj}")
        
        response = None

        if(RequestObj["command"]=="GETLOGINPAGE"):
            msg = "Login or Register"
            response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["LOGINPAGE"])
            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
        else:
            if(RequestObj["command"]=="LOGIN"):
                if(login(RequestObj["username"], RequestObj["password"])):
                    msg = "Login Success! Enjoy"
                    usertype, clientState = getClientState(RequestObj["username"])
                    response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
                else:
                    msg = "Invalid Username or Password"
                    response = myAppProtocol.Response(1, msg, LOC_CMD_MAP["LOGINPAGE"])
                myAppProtocol.sendAppProtocolPacket(clientSocket, response)
            
            
            elif(RequestObj["command"]=="REGISTER"):
                reg = register(RequestObj["username"], RequestObj["password"], RequestObj["usertype"])
                if(reg==1):
                    msg = "Successfully Registered!!!"
                    usertype, clientState = getClientState(RequestObj["username"])
                    response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
                elif(reg==2):
                    msg = "Username already exists."
                    response = myAppProtocol.Response(1, msg, LOC_CMD_MAP["LOGINPAGE"])
                else:
                    msg = "Registration Error!"
                    response = myAppProtocol.Response(1, msg, LOC_CMD_MAP["LOGINPAGE"])
                myAppProtocol.sendAppProtocolPacket(clientSocket, response)
            
            elif(RequestObj["command"]=="LOGOUT"):
                removeClientState(RequestObj["username"])
                msg = "Logged Out"
                response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["LOGINPAGE"])
                myAppProtocol.sendAppProtocolPacket(clientSocket, response)
            
            else:
                if(not authenticate(RequestObj["username"], RequestObj["password"])):
                    msg = "Authentication Failed"
                    response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["LOGINPAGE"])
                    myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                
                if(not isClientStatePresent(RequestObj["username"])):
                    msg = "User Session Expired"
                    response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["LOGINPAGE"])
                    myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                
                usertype, clientState = getClientState(RequestObj["username"])

                if(RequestObj["command"] in clientState["cmd_list"]):
                    if(RequestObj["command"]=="HOME"):
                        clientstate = None
                        if(usertype=="INSTRUCTOR"):
                            clientstate = createNewClientState("HOME_INSTRUCTOR", LOC_CMD_MAP["HOME_INSTRUCTOR"], -1)
                        else:
                            clientstate = createNewClientState("HOME_STUDENT", LOC_CMD_MAP["HOME_STUDENT"], -1)
                        saveClientState(RequestObj["username"], clientstate)
                        response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["LOGINPAGE"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    elif(RequestObj["command"]=="NEW POST"):
                        usertype, clientState = getClientState(RequestObj["username"])
                        if(clientState['class_id'] ==-1):
                            response = myAppProtocol.Response(1, "Login to a class first", clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        else:
                            createpost(clientState['class_id'],RequestObj["username"],RequestObj["postkeyword"],RequestObj["postcontent"])
                            saveClientState(RequestObj["username"], clientstate)
                            response = myAppProtocol.Response(0, "Posted Succesfully", LOC_CMD_MAP[LOCS[4]])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    elif(RequestObj["command"]=="GET ALL POSTS"):
                        usertype, clientState = getClientState(RequestObj["username"])
                        if(clientState['class_id'] ==-1):
                            response = myAppProtocol.Response(1, "Login to a class first", clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        else:
<<<<<<< Updated upstream
                            rows = getpost(clientState['class_id'],username)
                            response = myAppProtocol.Response(1, rows, clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
    
=======
                            clientstate = createNewClientState("INSIDECLASS_STUDENT", LOC_CMD_MAP["INSIDECLASS_STUDENT"], classroomId)
                            response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["INSIDECLASS_STUDENT"])
                        saveClientState(username, clientstate)
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    elif(RequestObj["command"]=="NEW POST"):
                        usertype, clientState = getClientState(RequestObj["username"])
                        if(clientState['class_id'] ==-1):
                            response = myAppProtocol.Response(1, "Login to a class first", clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        else:
                            createpost(clientState['class_id'],RequestObj["username"],RequestObj["postkeyword"],RequestObj["postcontent"])
                            saveClientState(RequestObj["username"], clientState)
                            response = myAppProtocol.Response(0, "Posted Succesfully", LOC_CMD_MAP[LOCS[4]])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    elif(RequestObj["command"]=="GET ALL POSTS"):
                        usertype, clientState = getClientState(RequestObj["username"])
                        if(clientState['class_id'] ==-1):
                            response = myAppProtocol.Response(1, "Login to a class first", clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        else:
                            rows = getpost(clientState['class_id'],RequestObj["username"])
                            response = myAppProtocol.Response(1, rows, clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    elif(RequestObj["command"]=="GET POST BY KEYWORD"):
                        usertype, clientState = getClientState(RequestObj["username"])
                        if(clientState['class_id'] ==-1):
                            response = myAppProtocol.Response(1, "Login to a class first", clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        else:
                            rows = getpostbykeyword(clientState['class_id'],RequestObj["username"],RequestObj["postkeyword"])
                            response = myAppProtocol.Response(1, rows, clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    # handle other commands
                    else:
                        response = myAppProtocol.Response(1, "Comming Soon", clientState["cmd_list"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    
                else:
                    response = myAppProtocol.Response(1, "Invalid Command", clientState["cmd_list"])
                    myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
    except Exception as e:
        response = myAppProtocol.Response(1, str(e), None)
        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
    finally:
        clientSocket.close()
        print(f"Connection from {address} has been terminated.")


# Creating TCP server socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Reusing same port
serverSocket.bind(('', DEFAULT_PORT))

serverSocket.listen(10) # Can establish upto 10 concurrent TCP Connections

# Temporary Database for saving onlineUsers
conn, c = getconnectiontodb()
# Create table if not exists
c.execute("CREATE TABLE IF NOT EXISTS onlineUsers (username text NOT NULL UNIQUE, usertype text NOT NULL, clientstate text NOT NULL);")
c.execute("DELETE FROM onlineUsers")
conn.commit()

# Listen for incomming connections
while True:
    clientSocket, address = serverSocket.accept()
    print(f"Connection from {address} has been established.")
    threading.Thread(target=handleClient, args=(clientSocket, address,)).start()

