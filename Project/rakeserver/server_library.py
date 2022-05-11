# import datetime
# import subprocess
import subprocess
import os 
import selectors
import socket

# Server objects manage execution/handling of client requests. 
class Server:
    def __init__(self, host, v=True):
        if v:print(" |-> [server]  Initialised rake server.")
        self.host      = host
        if v:print(" |-> [server]  Server data structures populated successfully.")

    def addSocket(self, SocketObject):
        self.socket = SocketObject

# Creates an object from parsed Rakefile information. 
class Parser:
    def __init__(self, path, v=True):
        # File details
        self.path   = path
        self.curdir = os.getcwd()

        # Connection details
        self.hosts  = list()
        self.actionsets = list()

        # Populates details data structures
        try:
            self.readRakefile()
        except:
            print(" |-> [parser]  Error: No Rakefile found!")
            print("\n[r.p] Execution ended due to an error.")
            exit()

        if v: self.printRakeDetails()

    # Prints all values held in the Parser object.
    def printRakeDetails(self):
        if self.actionsets and self.hosts :
            print(" |-> [parser]  Printing results...\n |")
            print(" |\tPORT:", self.port)
            print(" |\tHOSTS:", self.hosts)

            for actionNum, commands in enumerate(self.actionsets):
                print(" |\tactionset"+ str(actionNum+1))
                for i, command in enumerate(commands):
                    print(" |\t  " + str(i),command)
            print(" |\n |-> [parser]  Completed result printing.")
        else:
            print(" |-> [parser]  Cannot print; no Rakefile parsed!")

    # Performs parsing, populates data structures of Parser.
    def readRakefile(self):
        print(" |-> [parser]  Reading Rakefile...")
        with open(self.path, "r") as f:
            line = f.readline().replace("    ", "\t")   # Sets 4 spaces to tab character.

            while line:
                if line.startswith("actionset"):
                    commands = list()   # List of commands found in an ACTIONSETS.
                    line = f.readline().replace("    ", "\t")

                    # Commands/requirements of ACTIONSET must start with at least one tab.
                    while line.startswith("\t"):
                        if line.startswith("\tremote-"):  # Indicates command is executed remotely.
                            command = [ "remote",  line.strip().replace("remote-", "")]
                        else:                             # Indicates command is executed locally.
                            command = [ "local",   line.strip()]

                        # Increments line to check for potential requirements.
                        line = f.readline().replace("    ", "\t") 

                        if line.startswith("\t\t"):   # Requirement lines use two tab characters.
                            # Add requirements as list to the end of the command list.
                            command.append( line.replace("\t\trequires ", "").split() ) 
                            line = f.readline().replace("    ", "\t")
                        else:                         # No requirements for above command.
                            # Append empty list of requirements to the end of command list.
                            command.append( [] )
                            commands.append(command)  # Adds command above to current ACTIONSET commands.
                    self.actionsets.append(commands) # Adds commands of ACTIONSET to list of ACTIONSETS.
                else:
                    # Line holds PORT number, which is stored as an integer.
                    if line.startswith("#") or len(line.strip()) == 0:
                        None
                    elif line.startswith("PORT  ="):
                        # Default port for hosts with none specified.
                        self.port = line.replace("PORT  =","").strip()
                    # Line holds HOSTS, which are split and stored as a list.
                    elif line.startswith("HOSTS ="):
                        rawHosts = line.replace("HOSTS =","").split() 
                        # Where no port for host specified, the port 
                        #   found above is used. Port details should 
                        #   also be stored along with the name.
                        for host in rawHosts:
                            pair = host.split(":") 
                            if pair[0] == "localhost":
                                pair[0] = "127.0.0.1"
                            if len(pair) == 1:
                                pair.append(self.port)
                        # self.hosts is list of lists
                        self.hosts.append(":".join(pair)) # [0] hostname [1] port
                line = f.readline().replace("    ", "\t")
        print(" |-> [parser]  Read completed.")

# Allows for client-relative dir functions.
class DirectoryNavigator:
    def __init__(self, serverPath):
        self.defaultPath = serverPath + "/"

    # Creates a directory in current working directory.
    def createDir(self, dirName):
        print(" |-> [dirNav]  Creating '" + dirName+ "' in CD.")
        try: 
            os.mkdir(dirName)
            print(" |-> [dirNav]  Successfully created directory.")
            return dirName
        except FileExistsError:  # Thrown where dir exists
            print(" |-> [dirNav]  Directory already exists.")
        except: # Any other errors must halt execution 
            print(" |-> [dirNav]   ERROR: Cannot access or create directory.")
            exit()

        return os.getcwd() + "/" + dirName 

    # Get the path for a given host's temp directory.
    def getPath(self, host):
        return self.defaultPath + host + "_tmp"

# Handles header file sent to the client.
class DataTransmission:
    def __init__(self, select, sock, address):
        self.select             = select
        self.sock               = sock
        self.address            = address
        self.receive_buff       = b""
        self.send_buff          = b""
        self.request            = None
        self.response_created   = False
    
    def executeCommand(self, command):
        print(subprocess.check_output(command))

    def readData(self):
        try:
            data = self.sock.recv(4096)
        except BlockingIOError:
            pass
        else:
            if data:
                self.receive_buff += data
            else:
                raise RuntimeError("Peer closed.")

    def writeData(self):
        if self.request:
            if not self.response_created:
                # Binary or unknown content-type
                response = self._create_response_binary_content()
                message = self._create_message(response)
                self.response_created = True
                self.send_buff += message

        if self.send_buff:
            print(" |->[write]  Sending '"+self.send_buff+"' to '"+ self.address +"'")
            try:
                sent = self.sock.send(self.send_buff)
            except BlockingIOError:
                pass
            else:
                self.send_buff = self.send_buff[sent:]
                if sent and not self.send_buff:
                    self.close()

    def eventHandler(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()


# Used for management of socket functionality.
class SocketHandling:
    # Create a socket to communicate to server.
    def __init__(self, HOST, PORT):
        print(" |-> [socket]  Creating socket for '" + HOST+":" + str(PORT) + "'.")
        self.HOST, self.PORT = HOST, PORT
        self.select = selectors.DefaultSelector()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(" |-> [socket]  Successfully created socket.\n |")

    
    # Enable listening to the socket for communication.
    def initiateListening(self):
        print(" |-> [socket]  Enabling socket listening.")
        self.sock.bind((self.HOST, self.PORT))
        self.sock.listen()    
        self.sock.setblocking(False)
        self.select.register(self.sock, selectors.EVENT_READ, data=None)

        print(" |-> [socket]  Listening on '" + self.HOST + ":" + str(self.PORT) + "' enabled!")

    def acceptConnection(self, sock):
        connection, address = sock.accept()  
        connection.setblocking(False)
        print(" |-> [socket]  Accepted connection from '" + address + "'.")

        transmission = DataTransmission(self.select, connection, address)
        print(" |-> [socket]  Prepared data for transmission.")

        self.select.register(connection, selectors.EVENT_READ, data=transmission)

    def awaitClient(self):
        print(" |-> [socket]  Awaiting client commands...")
        try:
            while True:
                events = self.select.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.acceptConnection(key.fileobj)
                    else:
                        transmission = key.data
                        try:
                            transmission.eventHandler(mask)
                        except Exception:
                            print(" |-> [socket]  Error: An exception was thrown.")
                            transmission.close()
        except KeyboardInterrupt:
            print("\n |-> [socket]  Transmission halted by user.")
        finally:
            self.select.close()


if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'server.py'; file 'server_library.py' is a module only.")
  exit()
  