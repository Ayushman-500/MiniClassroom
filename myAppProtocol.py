COMMANDS= ["LOGIN", "REGISTER", "CREATECLASS", "POST", "JOINCLASS"]
USERTYPE = ["INSTRUCTOR", "STUDENT"]

class Request:
    def __init__(self, command, username, password):
        if command not in COMMANDS:
            raise Exception("Invalid Command")
        self.command = command
        self.username = username
        self.password = password
    
    def setregisterparams(self, usertype):
        if usertype not in USERTYPE:
            raise Exception("Invalid User Type")
        self.usertype = usertype
    
    def setnewclassparams(self, classname):
        self.classname = classname
    
    def setpostparams(self, postkeyword, postcontent, classid):
        self.postkeyword = postkeyword
        self.postcontent = postcontent
        self.classid = classid
    
    def setjoinclassparams(self, classid):
        self.classid = classid