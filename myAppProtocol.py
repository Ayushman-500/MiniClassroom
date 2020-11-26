import json

USERTYPE = ["INSTRUCTOR", "STUDENT"]
ENDPACKETPATTERN = '\r\n'

class Request:
    def __init__(self, command):
        self.dict = {"command":command}
    
    def setuserdetails(self, username, password):
        self.dict["username"] = username
        self.dict["password"] = password

    def __repr__(self):
        return json.dumps(self.dict)
    
    def setregisterparams(self, usertype):
        if usertype not in USERTYPE:
            raise Exception("Invalid User Type")
        self.dict["usertype"] = usertype
    
    def setnewclassparams(self, classname):
        self.dict["classname"] = classname
    
    def setpostparams(self, postkeyword, postcontent):
        self.dict["postkeyword"] = postkeyword
        self.dict["postcontent"] = postcontent
    
    def setjoinclassparams(self, classid):
        self.dict["classid"] = classid


class Response:
    def __init__(self, error, msg, cmd_list):
        self.dict = {"error":error, "message":msg, "cmd_list":cmd_list}
    
    def __repr__(self):
        return json.dumps(self.dict)


def receiveAppProtocolPacket(socket, buffer):
    packet = ""
    while True:
        msg = socket.recv(buffer)
        msg = msg.decode('utf-8')
        packet += msg
        if(len(msg)<=0 or packet.endswith(ENDPACKETPATTERN)):
            break
    packet = packet.rstrip(ENDPACKETPATTERN)
    return packet

def sendAppProtocolPacket(socket, AppProtocolObj):
    msg = repr(AppProtocolObj) + ENDPACKETPATTERN
    socket.send(bytes(msg,'utf-8'))


