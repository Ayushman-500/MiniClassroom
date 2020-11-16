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

def getconnectiontodb():
    conn = sqlite3.connect("./sqlitedb.db")
    cursor = conn.cursor()
    return conn, cursor


def authenticate(username, password):
    conn, c = getconnectiontodb()
    
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    rows = c.fetchall()

    if(len(rows)==0 or rows[0][0]!=password):
        return 0

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
    conn.commit()
    return 1


def createclass(classname):
    return 1


def handleClient(clientSocket, address):
    try:
        msg = myAppProtocol.receiveAppProtocolPacket(clientSocket, TCP_BUFFER)
        RequestObj = json.loads(msg)
        print(f"Received from {address}: {RequestObj}")
        
        response = None
        if(RequestObj["command"]=="LOGIN"):
            
            if(authenticate(RequestObj["username"], RequestObj["password"])):
                msg = "Login Success! Enjoy"
                response = myAppProtocol.Response(0, msg)
            else:
                msg = "Invalid Username or Password"
                response = myAppProtocol.Response(1, msg)
            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
        
        elif(RequestObj["command"]=="REGISTER"):
            reg = register(RequestObj["username"], RequestObj["password"], RequestObj["usertype"])
            if(reg==1):
                msg = "Successfully Registered!!!"
                response = myAppProtocol.Response(0, msg)
            elif(reg==2):
                msg = "Username already exists."
                response = myAppProtocol.Response(1, msg)
            else:
                msg = "Registration Error!"
                response = myAppProtocol.Response(1, msg)
            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
        
        elif(RequestObj["command"]=="CREATECLASS"):
            if(authenticate(RequestObj["username"], RequestObj["password"])):
                if(RequestObj["usertype"]=="INSTRUCTOR"):
                    if not createclass(RequestObj["classname"]):
                        msg = "Class creation failed :("
                        response = myAppProtocol.Response(1, msg)
                    else:
                        msg = "Class Successfully Created!!!"
                        response = myAppProtocol.Response(0, msg)
                else:
                    msg = "Students cannot create class"
                    response = myAppProtocol.Response(1, msg)
            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
        
        elif(RequestObj["command"]=="POST"):
            # todo
            return
        
        elif(RequestObj["command"]=="JOINCLASS"):
            # todo
            return
        
        else:
            msg = "Operation not available."
            response = myAppProtocol.Response(1, msg)
            myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
    except Exception as e:
        response = myAppProtocol.Response(1, str(e))
        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
    finally:
        clientSocket.close()
        print(f"Connection from {address} has been terminated.")


# Creating TCP server socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Reusing same port
serverSocket.bind(('', DEFAULT_PORT))

serverSocket.listen(10) # Can establish upto 10 concurrent TCP Connections

# Listen for incomming connections
while True:
    clientSocket, address = serverSocket.accept()
    print(f"Connection from {address} has been established.")
    threading.Thread(target=handleClient, args=(clientSocket, address,)).start()