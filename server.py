# Libraries
import socket
import pickle
import sys
import os
import threading
import time
import json
import myAppProtocol
import utils

# Constants
TCP_BUFFER = 1024
MAX_TCP_PAYLOAD = 1024
DEFAULT_PORT = 12345

def authenticate(username, password):
    
    return 1

def register(username, password, usertype):
    
    return 1

def createclass(classname):
    return 1

def handleClient(clientSocket, address):
    try:
        msg = utils.receivePacket(clientSocket, TCP_BUFFER)
        RequestObj = pickle.loads(msg)
        if(RequestObj.command=="LOGIN"):
            if(authenticate(RequestObj.username, RequestObj.password)):
                msg = "Login Success"
                clientSocket.sendall(bytes(msg,"utf-8"))
        elif(RequestObj.command=="REGISTER"):
            if(register(RequestObj.username, RequestObj.password, RequestObj.usertype)):
                msg = "Successfully Registered!!!"
                clientSocket.sendall(bytes(msg,"utf-8"))
        elif(RequestObj.command=="CREATECLASS"):
            if(authenticate(RequestObj.username, RequestObj.password)):
                if(RequestObj.usertype=="INSTRUCTOR"):
                    if not createclass(RequestObj.classname):
                        msg = "Class creation failed :("
                        clientSocket.sendall(bytes(msg,"utf-8"))
                    else:
                        msg = "Class Successfully Created!!!"
                        clientSocket.sendall(bytes(msg,"utf-8"))
                else:
                    msg = "Students cannot create class"
                    clientSocket.sendall(bytes(msg,"utf-8"))
        elif(RequestObj.command=="POST"):
            # todo
            return
        elif(RequestObj.command=="JOINCLASS"):
            # todo
            return
        else:
            msg = "Operation not available."
            clientSocket.sendall(bytes(msg,"utf-8"))
        
    except Exception as e:
        clientSocket.send(bytes(e, 'utf-8'))
    finally:
        clientSocket.close()


# Creating TCP server socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Reusing same port
serverSocket.bind(('', DEFAULT_PORT))

serverSocket.listen(10) # Can establish upto 10 concurrent TCP Connections

# Listen for incomming connections
while True:
    print("Waiting for Connection")
    clientSocket, address = serverSocket.accept()
    print(f"Connection from {address} has been established.")
    threading.Thread(target=handleClient, args=(clientSocket, address,)).start()