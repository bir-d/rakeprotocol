import os
import sys
import socket
import select
# import selectors

HEADER = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT".encode(FORMAT)


# Creates a directory inside the client directory.
def create_dir(dirName):
    print(" |-> [mkdir]  Creating '" + dirName+ "' in CD.")
    try: 
        os.mkdir(dirName)
        print(" |-> [mkdir]  Successfully created directory.")
    except FileExistsError:  # Thrown where dir exists
        print(" |-> [mkdir]  Directory already exists.")
    except: # Any other errors must halt execution 
        print(" |-> [mkdir]   ERROR: Cannot access or create directory.")
        exit()
    return os.getcwd() + "/" + dirName 

# Client objects manage connections to servers in the Rakefile.
class Client: 
    def __init__(self, rakefile_data):
        print(" |-> [client]  Initialised rake.p client.")
        self.ACTIONSETS             = rakefile_data.actionsets
        self.ADDRS, self.SERVERS    = list(), rakefile_data.hosts
        self.SOCKETS                = dict()

        # Makes dir for hosts; appends (host, port) to ADDRS
        for hostname in rakefile_data.hosts:
            create_dir(hostname+'_tmp')
            host, port = hostname.split(":")
            self.ADDRS.append((host, int(port)))
        print(" |-> [client]  Client data structures populated successfully.")

        self.nonblocking(self.ADDRS[0][0], self.ADDRS[0][1])
        # print(" |-> [client]  Establishing sockets for communication with hosts.")
        # for addr in self.ADDRS:
        #     self.connect_to_socket(addr[0], addr[1])

    # Creates and stores IPv4 socket for stream, then connects.
    #   - Is constant 'connection' okay, or should connection only 
    #     happen at the moment client sends?
    def connect_to_socket(self, addr):
        server = f"{addr[0]}:{addr[1]}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.SOCKETS[server] = sock
        sock.connect(addr)
        print(f" |-> [socket]  Opened and connected to socket at {server}.")
        
    # Sends message to socket at address
    #   - Do we need both sock and addr parameters to be passed?
    def send_message(self, sock, addr, message):
        # print(" |-> [send]  Sending message to server.")
        msg = message.encode(FORMAT)
        msg_len = len(msg)
        send_len = str(len(message)).encode("utf-8")
        send_len += b' ' * (HEADER - len(send_len))
        sock.send(send_len)
        sock.send(msg)
        # sock.send(DISCONNECT_MESSAGE)

        return len(send_len), msg_len


    def nonblocking(self, host, port):
        print("Connecting...")
        sock = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        connection = sock.connect_ex((host, port))
        if connection != 0:
            print("Failed to connect.")
            return 0

        sock.setblocking(False)
        inputs = [sock]
        outputs = [sock]

        while inputs:
            print("Waiting...")
            s_read, s_write, s_error = select.select(inputs, outputs, inputs, 1)
            
            for s in s_write:
                print("Sending...")
                message = "testMesssage"
                slen, msg_len = self.send_message(s, (host, port), message)
                print(f"> Sent {msg_len} bytes ({slen} header).")
                outputs.remove(s)

            for s in s_read:
                print("Reading...")
                data = s.recv(1024).decode("utf-8")
                print(f"Read '{data}' ({len(data)}).")
                print("Closing...")
                s.close()
                inputs.remove(s)
                break

            for s in s_error:
                print("Error occurred.")
                s_write.remove(s)
                outputs.remove(s)
                break
                

    def DEBUG_send(self, message):
        sock = self.SOCKETS[self.SERVERS[0]]
        addr = self.ADDRS[0]
        self.send_message(sock, addr, message)
        
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

    self.printRakeDetails()

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