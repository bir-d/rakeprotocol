from asyncore import read
from ctypes import addressof
import errno
import os
import socket
import sys
import re
import select

class Comms:
    HEADER = 64
    MAX_LEN = 1024
    FORMAT = 'utf-8'

class Codes:
    DISCONN_MSG     = "!D"
    COMMAND_MSG     = "!C"
    REQUEST_MSG     = "!R" 
    SUCCEED_RSP     = "!S"
    FAILURE_RSP     = "!F"
    EXECUTE_GET     = "!E"


# Client objects manage connections to servers in the Rakefile.
class Client: 
    def __init__(self, rakeData, v=True):
        print("[client]  Initialised rake.p client.")
        self.ACTIONSETS             = rakeData.actionsets
        # addrs   = (host str, port int)
        # servers = addrs.join()
        self.ADDRS, self.SERVERS    = list(), list()
        # sockets[server] = socket
        self.SOCKETS                = dict()
        #SOCKETS[SERVER[i]] = <socket object>
        # SERVER[i] = "127.0.0.1:5050"
        self.DIRPATH = os.getcwd()
        self.dirs = dict()

        for hostname in rakeData.hosts:
            # TODO:use single directory for communication responses
            self.dirs[hostname] = create_dir(hostname+'_tmp')
            self.SERVERS.append(hostname)
            host, port = hostname.split(":")
            self.ADDRS.append((host, int(port)))

        print("[client]  Establishing sockets for communication with hosts.")
        for addr in self.ADDRS:
            self.connect_to_socket(addr)
        print("[client]  Sockets connected.")

    def connect_to_socket(self, ADDR):
        SERVER = f"{ADDR[0]}:{ADDR[1]}" # check that addr[1] actually works
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)

        self.SOCKETS[SERVER] = sock
        sock.connect_ex(ADDR)
        print(f"[socket]  Opened and connected to socket at {SERVER}.")

    def send(self, socket, type, addr, val):
        if type == Codes.COMMAND_MSG:
            try:
                socket.sendall(type.encode(Comms.FORMAT))
                self.send_command(socket, val, addr)
                print(f"[command@{addr}] > {val} ")
            except Exception as e:
                print(f"Exception occurred while sending a command: {e}")
                exit()
        elif type == Codes.EXECUTE_GET:
            try:
                socket.sendall(type.encode(Comms.FORMAT))
                exec_cost = self.get_exec_cost(socket, addr)
                return exec_cost
            except Exception as e:
                print(f"Exception occurred while sending required files: {e}")
                exit()
        elif type == Codes.REQUEST_MSG:
            try:
                socket.sendall(type.encode(Comms.FORMAT))
                self.send_requirement(socket, val, addr)
            except Exception as e:
                print(f"Exception occurred while sending required files: {e}")
                exit()
        elif type == Codes.DISCONN_MSG:
            try:
                socket.sendall(type.encode(Comms.FORMAT))
            except Exception as e:
                print(f"Exception occurred while attempting to disconnect: {e}")
                exit()

    def send_requirement(self, socket, path, addr):
        name = path.split("/")[-1].encode(Comms.FORMAT) #b'test.txt'
        name_length = len(name) # 8
        send_name_length = str(name_length).encode(Comms.FORMAT) # b'8'
        send_name_length += b' ' * (Comms.HEADER - len(send_name_length)) # pads to 64

        with open(path) as f:
            msg = f.read()

        message = msg.encode(Comms.FORMAT)
        msg_length = len(message)
        send_msg_length = str(msg_length).encode(Comms.FORMAT)
        send_msg_length += b' ' * (Comms.HEADER - len(send_msg_length))

        socket.sendall(send_msg_length)
        socket.sendall(send_name_length)
        socket.sendall(name)
        socket.sendall(message)

        print(f"[files@{addr}] Sent '{name.decode(Comms.FORMAT)}'.")


    # ASSUMES THAT EXECUTION COST IS BASED ON THREADS SERVER IS RUNNING
    #   -   THIS MEANS THAT QUEUE LENGTH IS BY NUMBER OF ACTIVE CLIENTS
    #   -   THIS MEANS CLIENTS CANNOT RUN TWO COMMANDS AT THE SAME TIME
    #       AS THEY WILL BE UNDER THE SAME THREAD
    #   FIX might be to have a separate thread for each command sent?
    def recv_exec_cost(self,socket, addr):
        cost_len = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
        rec_cost_len = int(cost_len)
        exec_cost = socket.recv(rec_cost_len).decode(Comms.FORMAT)
        print(f"[{addr}] exec_cost = {exec_cost}")
        return exec_cost

    def send_command(self, socket, msg, addr):
        message = msg.encode(Comms.FORMAT) # b'echo hello cormac'
        msg_length = len(message)  # int:17
        send_length = str(msg_length).encode(Comms.FORMAT) # b'17'
        send_length += b' ' * (Comms.HEADER - len(send_length)) 

        # server: msg_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
        socket.sendall(send_length)
        #server: msg = conn.recv(msg_length).decode(Comms.FORMAT)
        socket.sendall(message)

    def recv_command(self, socket):
        rec_len = socket.recv(Comms.HEADER).decode(Comms.FORMAT) # b'12'
        result  = socket.recv(int(rec_len)) # receieves 12 bytes from server
        print(result)
        # # refactor as dirs no longer server based
        # try:
        #     os.chdir(self.dirs[addr])
        #     with open("log", 'a') as file:
        #         file.write(result.decode(Comms.FORMAT))
        # except IOError as e:
        #     if e.errno == errno.EPIPE:
        #         pass
        # else:
        #     os.chdir(self.DIRPATH)
        # finally:
        #     os.chdir(self.DIRPATH)


        
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
        print("[parser]  Error: No Rakefile found!")
        print("\n[r.p] Execution ended due to an error.")
        exit()

    if v: self.printRakeDetails()

  # Prints all values held in the Parser object.
  def printRakeDetails(self):
    if self.actionsets and self.hosts :
      print("[parser]  Printing results...\n|")
      print("|\tPORT:", self.port)
      print("|\tHOSTS:", self.hosts)

      for actionNum, commands in enumerate(self.actionsets):
        print("|\tactionset"+ str(actionNum+1))
        for i, command in enumerate(commands):
          print("|\t  " + str(i),command)
      print("|\n[parser]  Completed result printing.")
    else:
      print("[parser]  Cannot print; no Rakefile parsed!")

  # Performs parsing, populates data structures of Parser.
  def readRakefile(self):
    print("[parser]  Reading Rakefile...")
    with open(self.path, "r") as f:
        line = f.readline()   
        print(line)
        while line:
            if line.startswith("actionset"):
                commands = list()   # List of commands found in an ACTIONSETS.
                line = f.readline()

                # Commands/requirements of ACTIONSET must start with at least one tab.
                while line.startswith("\t"):
                    line = line.strip()
                    if line.startswith("remote-"):  # Indicates command is executed remotely.
                        command = [ "remote",  line.strip().replace("remote-", "")]
                    else:                             # Indicates command is executed locally.
                        command = [ "local",   line.strip()]
                    
                    line = f.readline()
                
                    if line.startswith("\t\t"):
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
        print("[parser]  Read completed.")


def create_dir(dirName, v=True):
    if v:print("[mkdir]  Creating '" + dirName+ "' in CD.")
    try: 
        os.mkdir(dirName)
        if v:print("[mkdir]  Successfully created directory.")
    except FileExistsError:  # Thrown where dir exists
        if v:print("[mkdir]  Directory already exists.")
    except: # Any other errors must halt execution 
        print("[mkdir]   ERROR: Cannot access or create directory.")
        exit()
    return os.getcwd() + "/" + dirName 




if __name__ == '__main__':
    # assumption that the client is in its own folder, and the rake is in the 
    #   folder above the client's folder
    default_path = "/".join(os.getcwd().split("/")[:-1]) + "/Rakefile"

    try:
        rakefile_path    = sys.argv[1]
        print("[r.p]\tUsing path given to find Rakefile.")
    except IndexError:
        rakefile_path    = default_path
        print("[r.p]\tNo Rakefile specified, using default path.")
        print(f"|\n|\t{default_path}\n|")
    except:
        print(f"[r.p]\tRakefile not found at path:\n\t'{sys.argv[1]}'")
        exit()

    # Extract information from Rakefile.
    rakefileData  = Parser(rakefile_path)

    # Uses Parser object to populate client data.
    print("\n[r.p]\tInstantiating client.")
    client   = Client(rakefileData)

    for actionset in client.ACTIONSETS:
        sockets_in_use = []
        for msg in actionset:
            # loop through sockets and get execution cost
            costs = []
            lowest = 0
            lowest_index = 0
            for index, addr in enumerate(client.SERVERS):
                exec_cost = int(client.send(client.SOCKETS[addr], Codes.EXECUTE_GET, addr, ""))
                costs.append(exec_cost)
                if exec_cost <= lowest:
                    lowest = exec_cost
                    lowest_index = index
            # TODO: THIS WILL BREAK IF THE LOWEST COST SERVER REFUSES OUR CONNECTION
        


            lowest_socket = client.SOCKETS[client.SERVERS[lowest_index]]   
            location, command, required = msg[0], msg[1], msg[2]

            for file in required:
                client.send(lowest_socket, Codes.REQUEST_MSG, client.SERVERS[lowest_index], file)

            client.send(lowest_socket, Codes.COMMAND_MSG, client.SERVERS[lowest_index], command)
            sockets_in_use.append(lowest_socket)            


            # check if any sockets readable
            readable = select.select(sockets_in_use, [], [])[0]
            if (readable != []):
                for sock in readable:
                    client.recv_command(sock)




    for addr in client.SERVERS:
        client.send(client.SOCKETS[addr], Codes.DISCONN_MSG, addr, "")
        print(f"\nDisconnected from {addr}.")
    
    
  