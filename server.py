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

LOCS = ["HOME_INSTRUCTOR", "HOME_STUDENT", "MYCLASSES", "INSIDECLASS_INSTRUCTOR", "INSIDECLASS_STUDENT"]

LOC_CMD_MAP = {"HOME_INSTRUCTOR":["CREATE CLASS", "MY CLASSES"], 
            "INSIDECLASS_INSTRUCTOR":["HOME","NEW POST","GET ALL POSTS","GET POST BY KEYWORD"],
            "HOME_STUDENT":["MY CLASSES"],
            "INSIDECLASS_STUDENT":["HOME","GET ALL POSTS", "GET POSTS BY KEYWORD"]}


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
    c.execute("DELETE FROM onlineUsers WHERE username=?", (username,))
    c.execute("INSERT INTO onlineUsers (username, usertype, clientstate) VALUES (?, ?, ?)", (username, usertype, client_state))
    conn.commit()

def getClientState(username):
    conn, c = getconnectiontodb()
    c.execute("SELECT * FROM onlineUsers WHERE username=?", (username,))
    rows = c.fetchall()
    client_state = json.loads(rows[0][2])
    return client_state



# Features of MiniClass

# Authentication and registration
def authenticate(username, password):
    conn, c = getconnectiontodb()
    
    c.execute("SELECT password,usertype FROM users WHERE username=?", (username,))
    rows = c.fetchall()

    if(len(rows)==0 or rows[0][0]!=password):
        return 0

    # Save client state
    clientstate = None
    if(rows[0][1]=="INSTRUCTOR"):
        clientstate = createNewClientState(LOCS[0], LOC_CMD_MAP[LOCS[0]], -1)
    else:
        clientstate = createNewClientState(LOCS[1], LOC_CMD_MAP[LOCS[1]], -1)
    saveClientState(username, clientstate)
    
    return 1

def register(username, password, usertype):
    conn, c = getconnectiontodb()

    # Create table if not exists
    c.execute("CREATE TABLE IF NOT EXISTS users (username text NOT NULL UNIQUE, password text, usertype text NOT NULL);")
    
    # check if same username already exists
    query = f"SELECT * FROM users WHERE username LIKE '{username}'"
    c.execute(query)
    rows = c.fetchall()
    if(len(rows)>0):
        return 2
    
    # insert new user into database
    c.execute("INSERT INTO users (username, password, usertype) VALUES (?, ?, ?)", (username, password, usertype))

    # Save client state
    clientstate = None
    if(rows[0][1]=="INSTRUCTOR"):
        clientstate = createNewClientState(LOCS[0], LOC_CMD_MAP[LOCS[0]], -1)
    else:
        clientstate = createNewClientState(LOCS[1], LOC_CMD_MAP[LOCS[1]], -1)
    saveClientState(username, clientstate)

    conn.commit()
    return 1


# Get, Create classes
def createclass(classname):
    # Create new class
    # Save client state with LOCS[2] and class_id=-1
    return 1

def getClass(classid):
    # Save client state with LOCS[3] or LOCS[4] with class_id!=-1 and updated cmd_list
    return 1

def getClassId(classname):
    class_id = None #replace None with class_id from classes database
    return class_id


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
        if(RequestObj["command"]=="LOGIN"):
            if(authenticate(RequestObj["username"], RequestObj["password"])):
                msg = "Login Success! Enjoy"
                clientState = getClientState(RequestObj["username"])
                response = myAppProtocol.Response(0, msg, clientState["cmd_list"])
            else:
                msg = "Invalid Username or Password"
                response = myAppProtocol.Response(1, msg, None)
            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
        
        elif(RequestObj["command"]=="REGISTER"):
            reg = register(RequestObj["username"], RequestObj["password"], RequestObj["usertype"])
            if(reg==1):
                msg = "Successfully Registered!!!"
                response = myAppProtocol.Response(0, msg)
            elif(reg==2):
                msg = "Username already exists."
                response = myAppProtocol.Response(1, msg, None)
            else:
                msg = "Registration Error!"
                response = myAppProtocol.Response(1, msg, None)
            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
        else:
            clientState = getClientState(RequestObj["username"])
            if(RequestObj["command"] in clientState["cmd_list"]):
                # todo: handle request
                return 
            else:
                response = myAppProtocol.Response(1, "Invalid Command", None)
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

