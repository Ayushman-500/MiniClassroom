def receivePacket(socket, buffer):
    packet = ""
    while True:
        msg = socket.recv(buffer)
        if(len(msg)<=0):
            break
        packet += msg
    
    return packet