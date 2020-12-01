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

MY_IP = sys.argv[1]

LOCS = ["LOGINPAGE", "HOME_INSTRUCTOR", "HOME_STUDENT", "MYCLASSES", "INSIDECLASS_INSTRUCTOR", "INSIDECLASS_STUDENT"]

LOC_CMD_MAP = {"LOGINPAGE":["LOGIN", "REGISTER"],
            "HOME_INSTRUCTOR":["CREATE CLASS", "MY CLASSES", "LOGOUT"],
            "MYCLASSES":["HOME"],
            "INSIDECLASS_INSTRUCTOR":["HOME","NEW POST","GET ALL POSTS","GET POST BY KEYWORD", "NEW DISCUSSION", "DISCUSSIONS", "GET DISCUSSION COMMENTS", "POST DISCUSSION COMMENT", "START SESSION", "LOGOUT"],
            "HOME_STUDENT":["JOIN CLASS", "MY CLASSES", "LOGOUT"],
            "INSIDECLASS_STUDENT":["HOME","GET ALL POSTS", "GET POST BY KEYWORD", "DISCUSSIONS", "GET DISCUSSION COMMENTS", "POST DISCUSSION COMMENT", "JOIN SESSION", "LOGOUT"],
            "SESSIONMODE":["GET SESSION USERS", "EXIT SESSION"]}

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
    query = "SELECT * FROM users WHERE username LIKE '{}'".format(username)
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

    # Save client state
    cmd_list = ["HOME"]
    for r in rows:
        cmd_list.append(r)
    clientState = None
    clientState = createNewClientState("MYCLASSES", cmd_list, -1)
    saveClientState(username, clientState)
    
    if (len(rows) == 0):
        return 2
    
    return 1


def getClassname(classroomId):
    conn, c = getconnectiontodb()
    c.execute("SELECT classname FROM classrooms WHERE classroomId =?", (classroomId,))
    classname = c.fetchall()[0][0]
    return classname


def getpost(class_id,username):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS posts"+ str(class_id)+" (id INTEGER PRIMARY KEY AUTOINCREMENT, classId INTEGER NOT NULL,username text NOT NULL,keyword text NOT NULL,Content text NOT NULL,date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);")
    finally:
        lock.release()
    query = "SELECT * FROM posts"+ str(class_id)+ " ORDER BY date DESC;"
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
        c.execute("INSERT INTO posts"+ str(class_id)+" (id, classId,username,keyword,Content,date) VALUES (NULL,?, ?,?,?,?)", (class_id,username, keyword, Content,datetime.datetime.now()))
        conn.commit()
    finally:
        lock.release()
    return 1


def getpostbykeyword(class_id,username,keyword):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS posts"+ str(class_id)+" (id INTEGER PRIMARY KEY AUTOINCREMENT, classId INTEGER NOT NULL,username text NOT NULL,    text NOT NULL,Content text NOT NULL,date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);")
    finally:
        lock.release()
    query = "SELECT * FROM posts"+ str(class_id)+ " WHERE keyword LIKE '" + str(keyword) + "' ORDER BY date DESC;"
    c.execute(query)
    rows = c.fetchall()
    json_output = json.dumps(rows)
    return(json_output)
    


def createDiscussion(username, class_id, topic):
    conn, c = getconnectiontodb()
 
    try:
        lock.acquire()
        
        c.execute("CREATE TABLE IF NOT EXISTS discussions (discussionID INTEGER PRIMARY KEY AUTOINCREMENT, \
                    topic text NOT NULL, classID INTEGER NOT NULL);")
        
        c.execute("INSERT INTO discussions (topic, classID) VALUES (?, ?)", (topic, class_id,))
        conn.commit()
    finally:
        lock.release()
    
    return 1

def getClassDiscussions(username, class_id):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        c.execute("CREATE TABLE IF NOT EXISTS discussions (discussionID INTEGER PRIMARY KEY AUTOINCREMENT, \
                    topic text NOT NULL, classID INTEGER NOT NULL);")
    finally:
        lock.release()
    
    query = "SELECT discussionID, topic FROM discussions WHERE classID = '{}'".format(class_id)
    c.execute(query)
    rows = c.fetchall()
    return json.dumps(rows)

def postDiscussionComment(username, disscussion_id, comment_type, comment):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS comments (username text NOT NULL, discussionID INTEGER NOT NULL, comment_type text NOT NULL, comment text, date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);")

        c.execute("INSERT INTO comments (username, discussionID, comment_type, comment, date) VALUES (?,?,?,?,?)", (username, disscussion_id, comment_type, comment, datetime.datetime.now()))
        conn.commit()
    finally:
        lock.release()
    return 1

def getDiscussionComments(username, discusssion_id):
    conn, c = getconnectiontodb()
    try:
        lock.acquire()
        # Create table if not exists
        c.execute("CREATE TABLE IF NOT EXISTS comments (username text NOT NULL, discussionID INTEGER NOT NULL, comment_type text NOT NULL, comment text, date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);")

    finally:
        lock.release()
        
    query = None
    if(getUserType(username)=="INSTRUCTOR"):
        query = "SELECT * FROM comments WHERE discussionID = '{}'".format(discusssion_id)
    else:
        query = "SELECT * FROM comments WHERE discussionID = '{}' AND (username = '{}' OR comment_type = 'PUBLIC')".format(discusssion_id,username)
    c.execute(query)
    rows = c.fetchall()
    return json.dumps(rows)

def checkDisscussionIDinClassID(discussion_id, class_id):
    conn, c = getconnectiontodb()
 
    try:
        lock.acquire()
        c.execute("CREATE TABLE IF NOT EXISTS discussions (discussionID INTEGER PRIMARY KEY AUTOINCREMENT, \
                    topic text NOT NULL, classID INTEGER NOT NULL);")
    finally:
        lock.release()
    
    c.execute("SELECT * from discussions WHERE discussionID = ? AND classID = ?", (discussion_id, class_id,))
    rows = c.fetchall()
    if(len(rows)==0):
        return 0
    return 1


def createNewSession(username, ip, port, class_id):
    if(getUserType(username)!="INSTRUCTOR"):
        return 0

    conn, c = getconnectiontodb()
 
    try:
        lock.acquire()
        
        c.execute("CREATE TABLE IF NOT EXISTS sessions (classID INTEGER NOT NULL, \
                    username text NOT NULL, ip text NOT NULL, port text NOT NULL);")
        
        c.execute("INSERT INTO sessions (classID, username, ip, port) VALUES (?, ?, ?, ?)", (class_id, username, ip, port,))
        conn.commit()
    finally:
        lock.release()
    
    return 1

def joinSession(username, ip, port, class_id):
    conn, c = getconnectiontodb()

    try:
        lock.acquire()
        
        c.execute("CREATE TABLE IF NOT EXISTS sessions (classID INTEGER NOT NULL, \
                    username text NOT NULL, ip text NOT NULL, port text NOT NULL);")
    finally:
        lock.release()

    c.execute("SELECT * FROM sessions WHERE classID = ?",(class_id,))
    rows = c.fetchall()
    if(len(rows)==0):
        return 0

    try:
        lock.acquire()

        c.execute("INSERT INTO sessions (classID, username, ip, port) VALUES (?, ?, ?, ?)", (class_id, username, ip, port,))
        conn.commit()
    finally:
        lock.release()
    
    return 1

def exitSession(ip, port, class_id):
    conn, c = getconnectiontodb()

    try:
        lock.acquire()

        c.execute("DELETE FROM sessions WHERE classID = ? AND ip = ? AND port = ?",(class_id, ip, port,))
        conn.commit()
    finally:
        lock.release()
    
    return 1

def getSessionUsers(class_id):
    conn, c = getconnectiontodb()

    c.execute("SELECT username, ip, port FROM sessions WHERE classID = ?",(class_id,))
    rows = c.fetchall()
    
    return json.dumps(rows)



def handleClient(clientSocket, address):
    try:
        msg = myAppProtocol.receiveAppProtocolPacket(clientSocket, TCP_BUFFER)
        RequestObj = json.loads(msg)
        print("Received from {}: {}".format(address,RequestObj))
        
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
                    

                    elif(RequestObj["command"]=="NEW DISCUSSION"):
                        class_id = clientState["class_id"]
                        result = createDiscussion(RequestObj["username"], class_id, RequestObj["discussion_topic"])
                        response = None
                        if(result==1):
                            msg = "Discussion created Successfully!!!"
                            response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
                        else:
                            msg = "Error in creating Discussion. Try Again."
                            response = myAppProtocol.Response(1, msg, clientState["cmd_list"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)

                    elif(RequestObj["command"]=="DISCUSSIONS"):
                        class_id = clientState["class_id"]
                        result = getClassDiscussions(RequestObj["username"], class_id)
                        response = myAppProtocol.Response(0, result, clientState["cmd_list"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    
                    elif(RequestObj["command"]=="GET DISCUSSION COMMENTS"):
                        class_id = clientState["class_id"]
                        if(checkDisscussionIDinClassID(RequestObj["discussion_id"], class_id)):
                            result = getDiscussionComments(RequestObj["username"], RequestObj["discussion_id"])
                            response = myAppProtocol.Response(0, result, clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        else:
                            result = "Please Enter Valid Discussion ID"
                            response = myAppProtocol.Response(1, result, clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)

                    elif(RequestObj["command"]=="POST DISCUSSION COMMENT"):
                        class_id = clientState["class_id"]
                        if(checkDisscussionIDinClassID(RequestObj["discussion_id"], class_id)):
                            result = postDiscussionComment(RequestObj["username"], RequestObj["discussion_id"], RequestObj["comment_type"], RequestObj["comment"])
                            if(result==1):
                                msg = "Posted Discussion Comment Successfully!!!"
                                response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
                            else:
                                msg = "Error in Commenting. Try Again."
                                response = myAppProtocol.Response(1, msg, clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        else:
                            result = "Please Enter Valid Discussion ID"
                            response = myAppProtocol.Response(1, result, clientState["cmd_list"])
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                        
                    elif(RequestObj["command"]=="START SESSION"):
                        class_id = clientState["class_id"]
                        result = createNewSession(RequestObj["username"], RequestObj["ip"], RequestObj["port"] ,class_id)
                        if(result):
                            msg = "Session Created Successfully!!!"
                            clientstate = createNewClientState("SESSIONMODE", LOC_CMD_MAP["SESSIONMODE"],class_id)
                            saveClientState(RequestObj["username"], clientstate)
                            response = myAppProtocol.Response(0, msg, clientstate["cmd_list"])
                        else:
                            msg = "Error: Session cannot be Created."
                            response = myAppProtocol.Response(1, msg, clientState["cmd_list"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    
                    elif(RequestObj["command"]=="JOIN SESSION"):
                        class_id = clientState["class_id"]
                        result = joinSession(RequestObj["username"], RequestObj["ip"], RequestObj["port"], class_id)
                        if(result):
                            msg = "Joined Session Successfully!!!"
                            clientstate = createNewClientState("SESSIONMODE", LOC_CMD_MAP["SESSIONMODE"],class_id)
                            saveClientState(RequestObj["username"], clientstate)
                            response = myAppProtocol.Response(0, msg, clientstate["cmd_list"])
                        else:
                            msg = "No session available."
                            response = myAppProtocol.Response(1, msg, clientState["cmd_list"])
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    
                    elif(RequestObj["command"]=="EXIT SESSION"):
                        class_id = clientState["class_id"]
                        result = exitSession(RequestObj["ip"], RequestObj["port"], class_id)
                        if(result):
                            msg = "Session Exited"
                            if (usertype=="INSTRUCTOR"):
                                clientstate = createNewClientState("INSIDECLASS_INSTRUCTOR", LOC_CMD_MAP["INSIDECLASS_INSTRUCTOR"], class_id)
                                response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["INSIDECLASS_INSTRUCTOR"])
                            else:
                                clientstate = createNewClientState("INSIDECLASS_STUDENT", LOC_CMD_MAP["INSIDECLASS_STUDENT"], class_id)
                                response = myAppProtocol.Response(0, msg, LOC_CMD_MAP["INSIDECLASS_STUDENT"])
                            saveClientState(RequestObj["username"], clientstate)
                            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    
                    elif(RequestObj["command"]=="GET SESSION USERS"):
                        class_id = clientState["class_id"]
                        result = getSessionUsers(class_id)
                        response = myAppProtocol.Response(0, result, clientState["cmd_list"])
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
        print("Connection from {} has been terminated.".format(address))


# Creating TCP server socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Reusing same port
ip = socket.gethostbyname(socket.gethostname())
serverSocket.bind((MY_IP, DEFAULT_PORT))

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
    print("Connection from {} has been established.".format(address))
    threading.Thread(target=handleClient, args=(clientSocket, address,)).start()

