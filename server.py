# Libraries
import socket
import sys
import os
import threading
import time
import json
import myAppProtocol
import sqlite3

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
            "INSIDECLASS_STUDENT":["HOME","GET ALL POSTS", "GET POST BY KEYWORD", "LOGOUT"]}

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


# Create classes
def createClass(username, classname):
    conn, c = getconnectiontodb()
 
    try:
        lock.acquire()
        # Create the metadata about class if not already exists
        c.execute("CREATE TABLE IF NOT EXISTS classrooms (classroomId INTEGER PRIMARY KEY AUTOINCREMENT, \
                    username text NOT NULL, classname text NOT NULL);")
        # Insert the new class into the metadata
        c.execute("INSERT INTO classrooms (username, classname) VALUES (?, ?)", (username, classname,))
        # Get the id of the last inserted row
        c.execute("SELECT classroomId FROM classrooms ORDER BY classroomId DESC LIMIT 1;")
        classroomId = c.fetchall()[0][0]
        # Creating the table for that classroom
        query = "CREATE TABLE `{}_{}` (postId INTEGER PRIMARY KEY AUTOINCREMENT, \
            postContent text NOT NULL, discussionId INTEGER NOT NULL, discussionContent text NOT NULL)".format(classname, classroomId)
        c.execute(query)
        conn.commit()
    finally:
        lock.release()

    # From here we will go to my classes and thus save the state accordingly
    usertype = getUserType(username)
    return myClasses(username, usertype)

def joinClass(classroomId, username):
    conn, c = getconnectiontodb()
    c.execute("SELECT * FROM classrooms WHERE classroomId=?", (classroomId,))
    rows = c.fetchall()
    if (len(rows)==0):
        return 2
    
    try:
        lock.acquire()
        # Create the metadata about the classroomMembers if not exists
        c.execute("CREATE TABLE IF NOT EXISTS classroomMembers (classroomId integer UNSIGNED NOT NULL,\
                    username text NOT NULL);")
        conn.commit()
    finally:
        lock.release()

    # From here we will go to my classes and get the current classes the user is enrolled in
    usertype = getUserType(username)
    myClasses(username, usertype)

    # checking if the student is already enrolled in this class
    usertype, clientState = getClientState(username)
    for pos in range(1,len(list(clientState["cmd_list"]))):
        if clientState["cmd_list"][pos][1]==classroomId:
            return 3
    
    try:
        lock.acquire()
        # Entering that user into that classroom
        c.execute("INSERT INTO classroomMembers (classroomId, username) VALUES (?, ?)", (classroomId, username,))
        conn.commit()
    finally:
        lock.release()

    # Updating the client state for the joined class
    classname = getClassname(classroomId)
    clientState["cmd_list"].append([classname, classroomId])
    saveClientState(username, clientState)
    return 1


def myClasses(username, usertype):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create the metadata about class if not already exists
        c.execute("CREATE TABLE IF NOT EXISTS classrooms (classroomId INTEGER PRIMARY KEY AUTOINCREMENT, \
                    username text NOT NULL, classname text NOT NULL);")
        c.execute("CREATE TABLE IF NOT EXISTS classroomMembers (classroomId integer UNSIGNED NOT NULL,\
                    username text NOT NULL);")
        conn.commit()
    finally:
        lock.release()
    

    if (usertype == "STUDENT"):
        c.execute("SELECT classname, classroomid FROM classrooms WHERE classroomId in \
                    (SELECT classroomId FROM classroomMembers WHERE username=?)", (username,))
        rows = c.fetchall()
    else:
        c.execute("SELECT classname, classroomid FROM classrooms WHERE username=?", (username,))
        rows = c.fetchall()
    
    if (len(rows) == 0):
        return 2
    
    # Save client state
    cmd_list = ["HOME"]
    for r in rows:
        cmd_list.append(r)
    clientState = None
    clientState = createNewClientState("MYCLASSES", cmd_list, -1)
    saveClientState(username, clientState)
    return 1


def getClassname(classroomId):
    conn, c = getconnectiontodb()
    c.execute("SELECT classname FROM classrooms WHERE classroomId =?", (classroomId,))
    classname = c.fetchall()[0][0]
    return classname


# Get Create Posts
def createpost():
    # Create new post with class_id from clientstate in onlineUsers db
    # Save client state with LOCS[3]
    return 1
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
                        clientState = None
                        if(usertype=="INSTRUCTOR"):
                            clientState = createNewClientState("HOME_INSTRUCTOR", LOC_CMD_MAP["HOME_INSTRUCTOR"], -1)
                        else:
                            clientState = createNewClientState("HOME_STUDENT", LOC_CMD_MAP["HOME_STUDENT"], -1)
                        saveClientState(RequestObj["username"], clientState)
                        response = myAppProtocol.Response(0, "", clientState["cmd_list"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)


                    elif (RequestObj["command"]=="CREATE CLASS"):
                        username, classname = RequestObj["username"], RequestObj["classname"]
                        if (createClass(username, classname)):
                            usertype, clientState = getClientState(RequestObj["username"])
                            msg = "New class {} created successfully".format(classname) + "\n\n" + \
                                "Here is the list of your current classrooms"
                            response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
                        else:
                            msg = "Error while creating class {}".format(classname)
                            response = myAppProtocol.Response(1, msg, LOC_CMD_MAP["HOME_INSTRUCTOR"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)

                    elif (RequestObj["command"]=="JOIN CLASS"):
                        username, classroomId = RequestObj["username"], RequestObj["classid"]
                        result = joinClass(classroomId, username)
                        usertype, clientState = getClientState(RequestObj["username"])
                        if (result==2):
                            msg = "No classroom for this code {}".format(classroomId) 
                            response = myAppProtocol.Response(1, msg, LOC_CMD_MAP["HOME_STUDENT"])
                        elif (result==3):
                            classname = getClassname(classroomId) + "_" + str(classroomId)
                            msg = "You are already enrolled in the classroom {}".format(classname) + "\n\n" + \
                                "Here is the list of your current classrooms"
                            response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
                        elif (result==1):
                            classname = getClassname(classroomId) + "_" + str(classroomId)
                            msg = "You are successfully enrolled in the classroom {}".format(classname) + "\n\n" + \
                                "Here is the list of your current classrooms"
                            response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
                        else:
                            msg = "Error while joining the class via code{}".format(classroomId)
                            response = myAppProtocol.Response(1, msg, LOC_CMD_MAP["HOME_INSTRUCTOR"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)

                    elif (RequestObj["command"]=="MY CLASSES"):
                        username = RequestObj["username"]
                        usertype = getUserType(username)
                        result = myClasses(username, usertype)
                        if (result==1):
                            usertype, clientState = getClientState(RequestObj["username"])
                            msg = "Here is the list of your current classrooms"
                            response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
                        else:
                            if (result==2):
                                msg = "You have no classroom for now"
                            else:
                                msg = "Error while showing the list of classrooms"
                            if (usertype=="INSTRUCTOR"):
                                response = myAppProtocol.Response(1, msg, LOC_CMD_MAP["HOME_INSTRUCTOR"])
                            else:
                                response = myAppProtocol.Response(1, msg, LOC_CMD_MAP["HOME_STUDENT"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)

                    elif (clientState["loc"]=="MYCLASSES"):
                        username = RequestObj["username"]
                        usertype = getUserType(username)
                        classroomId = RequestObj["command"][1]
                        classroom = getClassname(classroomId) + "_" + str(classroomId)
                        msg = "Welcome to the classroom {}".format(classroom)
                        clientstate = None
                        if (usertype=="INSTRUCTOR"):
                            clientstate = createNewClientState("INSIDECLASS_INSTRUCTOR", LOC_CMD_MAP["INSIDECLASS_INSTRUCTOR"], classroomId)
                            response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["INSIDECLASS_INSTRUCTOR"])
                        else:
                            clientstate = createNewClientState("INSIDECLASS_STUDENT", LOC_CMD_MAP["INSIDECLASS_STUDENT"], classroomId)
                            response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["INSIDECLASS_STUDENT"])
                        saveClientState(username, clientstate)
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        


                    
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
ip = socket.gethostbyname(socket.gethostname())
serverSocket.bind((ip, DEFAULT_PORT))

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

