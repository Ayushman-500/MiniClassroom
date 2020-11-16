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

def getcursortodb():
    conn = sqlite3.connect("./sqlitedb.db")
    c = conn.cursor()
    return c


def authenticate(username, password):

    return 1

def register(username, password, usertype):
    # c = getcursortodb()
    # c.execute("CREATE TABLE IF NOT EXISTS users ( id integer PRIMARY KEY AUTOINCREMENT, username text NOT NULL, password text, usertype text NOT NULL);")
    print("Registering")
    return 1

def createclass(classname):
    return 1

def handleClient(clientSocket, address):
    try:
        msg = myAppProtocol.receiveAppProtocolPacket(clientSocket, TCP_BUFFER)
        RequestObj = json.loads(msg)
        print(f"Received from {address}: {RequestObj}")
        print(RequestObj["command"])
        
        if(RequestObj["command"]=="LOGIN"):
            if(authenticate(RequestObj["username"], RequestObj["password"])):
                msg = "Login Success"
                response = myAppProtocol.Response(0, msg)
                myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
        elif(RequestObj["command"]=="REGISTER"):
            if(register(RequestObj["username"], RequestObj["password"], RequestObj["usertype"])):
                msg = "Successfully Registered!!!"
                response = myAppProtocol.Response(0, msg)
                myAppProtocol.sendAppProtocolPacket(clientSocket, response)
        
        elif(RequestObj["command"]=="CREATECLASS"):
            if(authenticate(RequestObj["username"], RequestObj["password"])):
                if(RequestObj["usertype"]=="INSTRUCTOR"):
                    if not createclass(RequestObj["classname"]):
                        msg = "Class creation failed :("
                        response = myAppProtocol.Response(1, msg)
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
                    else:
                        msg = "Class Successfully Created!!!"
                        response = myAppProtocol.Response(0, msg)
                        myAppProtocol.sendAppProtocolPacket(clientSocket, response)
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
        clientSocket.send(bytes(str(e), 'utf-8'))
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