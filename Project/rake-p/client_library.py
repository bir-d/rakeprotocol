from email import header
import os
import socket
import selectors
import sys

HEADER = 64
FORMAT = 'utf-8'

def create_dir(dirName, v=True):
    if v:print(" |-> [mkdir]  Creating '" + dirName+ "' in CD.")
    try: 
        os.mkdir(dirName)
        if v:print(" |-> [mkdir]  Successfully created directory.")
    except FileExistsError:  # Thrown where dir exists
        if v:print(" |-> [mkdir]  Directory already exists.")
    except: # Any other errors must halt execution 
        print(" |-> [mkdir]   ERROR: Cannot access or create directory.")
        exit()
    return os.getcwd() + "/" + dirName 

# Client objects manage connections to servers in the Rakefile.
class Client: 
    def __init__(self, rakeData, v=True):
        print(" |-> [client]  Initialised rake.p client.")
        self.ACTIONSETS             = rakeData.actionsets
        self.ADDRS, self.SERVERS    = list(), list()
        self.SOCKETS                = dict()

        for hostname in rakeData.hosts:
            create_dir(hostname+'_tmp')
            self.SERVERS.append(hostname)
            host, port = hostname.split(":")
            self.ADDRS.append((host, int(port)))
        print(" |-> [client]  Client data structures populated successfully.")

        print(" |-> [client]  Establishing sockets for communication with hosts.")
        for ADDR in self.ADDRS:
            self.connect_to_socket(ADDR)

    def connect_to_socket(self, ADDR):
        SERVER = f"{ADDR[0]}:{ADDR[1]}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SOCKETS[SERVER] = sock
        sock.connect(ADDR)
        print(f" |-> [socket]  Opened and connected to socket at {SERVER}.")

    def send_message(self, sock, message):
        print(" |-> [send]  Sending message to server.")
        msg = message.encode(FORMAT)
        msg_len = len(msg)
        send_len = str(msg_len).encode(FORMAT)
        send_len += b' ' * (HEADER - len(send_len))
        sock.send(send_len)
        sock.send(msg)
        
        # revise this line
        print(" |-> [read]  Getting Server response.\n")
        print(sock.recv(2048).decode(FORMAT))


    def DEBUG_send(self, message):
        sock = self.SOCKETS[self.SERVERS[0]]
        self.send_message(sock, message)
        

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
                    else:   # No requirements for above command.
                        # Append empty list of requirements to the end of command list.
                        command.append( [] )
                        commands.append(command)  # Adds command above to current ACTIONSET commands.
                self.actionsets.append(commands) # Adds commands of ACTIONSET to list of ACTIONSETS.
            else:
                # Line holds port number, which is stored as an integer.
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

if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'client.py'; file 'client_library.py' is a module only.")
  exit()