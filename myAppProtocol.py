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
    
    def setnewdiscussionparams(self, topic):
        self.dict["discussion_topic"] = topic
    
    def setgetcommentsparams(self, discussion_id):
        self.dict["discussion_id"] = discussion_id
    
    def setnewcommentparams(self, discussion_id, comment_type, comment):
        self.dict["discussion_id"] = discussion_id
        self.dict["comment_type"] = comment_type
        self.dict["comment"] = comment

    def setsessiondetails(self, ip, port):
        self.dict["ip"] = ip
        self.dict["port"] = port

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


