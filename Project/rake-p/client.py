import os
import socket
import sys
import re

class Comms:
    HEADER = 64
    FORMAT = 'utf-8'

class Codes:
    DISCONN_MSG     = "!D"
    COMMAND_MSG     = "!C"
    REQUEST_MSG     = "!R"
    SUCCEED_RSP     = "!S"
    FAILURE_RSP     = "!F"

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

        print(" |-> [client]  Establishing sockets for communication with hosts.")
        for addr in self.ADDRS:
            print(f"> {addr}")
            self.connect_to_socket(addr)
        print(" |-> [client]  Sockets connected.")

    def connect_to_socket(self, ADDR):
        SERVER = f"{ADDR[0]}:{ADDR[1]}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SOCKETS[SERVER] = sock
        sock.connect(ADDR)
        print(f" |-> [socket]  Opened and connected to socket at {SERVER}.")

    def send(self, socket, type, val=""):
        if type == Codes.COMMAND_MSG:
            socket.send(type.encode(Comms.FORMAT))
            self.send_command(socket, val)
        elif type == Codes.REQUEST_MSG:
            socket.send(type.encode(Comms.FORMAT))
            self.send_requirement(socket, val)
        elif type == Codes.DISCONN_MSG:
            socket.send(type.encode(Comms.FORMAT))

    def send_requirement(self, socket, path):
        name = path.split("/")[-1].encode(Comms.FORMAT)
        name_length = len(name)
        send_name_length = str(name_length).encode(Comms.FORMAT)
        send_name_length += b' ' * (Comms.HEADER - len(send_name_length))

        with open(path) as f:
            msg = f.read()
        message = msg.encode(Comms.FORMAT)
        msg_length = len(message)
        send_msg_length = str(msg_length).encode(Comms.FORMAT)
        send_msg_length += b' ' * (Comms.HEADER - len(send_msg_length))

        socket.send(send_msg_length)
        socket.send(send_name_length)
        socket.send(name)
        socket.send(message)
        
        if socket.recv(2).decode(Comms.FORMAT) == Codes.SUCCEED_RSP:
            print(f"[r.s] File '{name.decode(Comms.FORMAT)}' received.")
        elif socket.recv(2).decode(Comms.FORMAT) == Codes.FAILURE_RSP:
            print("[r.s] An error occurred while receiving.")

    def send_command(self, socket, msg):
        message = msg.encode(Comms.FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(Comms.FORMAT)
        send_length += b' ' * (Comms.HEADER - len(send_length))
        socket.send(send_length)
        socket.send(message)
        
        if socket.recv(2).decode(Comms.FORMAT) == Codes.SUCCEED_RSP:
            print("[r.s] Command executed successfully.")
            # receive_output_len()
            # receive_output_message()

        elif socket.recv(2).decode(Comms.FORMAT) == Codes.FAILURE_RSP:
            print("[r.s] An error occurred in command execution.")
            # halt_execution()



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
        line = f.readline().strip()   # Sets 4 spaces to tab character.

        while line:
            line = line.strip()

            if line.startswith("actionset"):
                commands = list()   # List of commands found in an ACTIONSETS.
                line = f.readline()

                # Commands/requirements of ACTIONSET must start with at least one tab.
                while re.match(r'[ \t]', line):
                    line = line.strip()
                    if line.startswith("remote-"):  # Indicates command is executed remotely.
                        command = [ "remote",  line.strip().replace("remote-", "")]
                    else:                             # Indicates command is executed locally.
                        command = [ "local",   line.strip()]
                    
                    line = f.readline()
                
                    if re.match(r'[ \t\t]', line):
                        line = line.strip()
                        command.append( line.replace("requires ", "").split() ) 
                        line = f.readline()
                    else:   # No requirements for above command.
                            # Append empty list of requirements to the end of command list.
                        command.append( [] )
                    commands.append(command)  # Adds command above to current ACTIONSET commands.
                self.actionsets.append(commands) # Adds commands of ACTIONSET to list of ACTIONSETS.
            else:
                # Line holds port number, which is stored as an integer.
                if line.startswith("#") or line.isspace():
                    None
                elif line.startswith("PORT  = "):
                    # Default port for hosts with none specified.
                    self.port = line.replace("PORT  = ","").strip()
                # Line holds HOSTS, which are split and stored as a list.
                elif line.startswith("HOSTS ="):
                    rawHosts = line.replace("HOSTS = ","").split() 
                    for host in rawHosts:
                        pair = host.split(":") 
                        if len(pair) == 1:
                            pair.append(self.port)
                        self.hosts.append(":".join(pair)) # [0] hostname [1] port
            line = f.readline()
        print(" |-> [parser]  Read completed.")

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

if __name__ == '__main__':
    default_path = "/".join(os.getcwd().split("/")[:-1]) + "/Rakefile"

    try:
        rakefile_path    = sys.argv[1]
        print("[r.p]\tUsing path given to find Rakefile.")
    except IndexError:
        rakefile_path    = default_path
        print("[r.p]\tNo Rakefile specified, using default path.")
        print(f" |\n |\t{default_path}\n |")
    except:
        print(f"[r.p]\tRakefile not found at path:\n\t'{sys.argv[1]}'")
        exit()

    # Extract information from Rakefile.
    rakefileData  = Parser(rakefile_path)


    # Uses Parser object to populate client data.
    print("\n[r.p]\tInstantiating client.")
    client   = Client(rakefileData)

    # TESTING
    test_socket = client.SOCKETS[client.SERVERS[0]]

    for actionset in client.ACTIONSETS:
        for msg in actionset:
            location, command, required = msg[0], msg[1], msg[2]

            for file in required:
                client.send(test_socket, Codes.REQUEST_MSG, file)
            client.send(test_socket, Codes.COMMAND_MSG, command)
        client.send(test_socket, Codes.DISCONN_MSG, "")
    
    
  