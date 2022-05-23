from asyncore import read, socket_map
from ctypes import addressof
import errno
import os
import socket
import sys
import re
import select

class Comms:
    HEADER = 64
    CODE = 2
    RESPONSETYPES = 3
    MAX_LEN = 1024
    FORMAT = 'utf-8'

class Codes:
    DISCONN_MSG     = "!D"
    COMMAND_MSG     = "!C"
    REQUEST_MSG     = "!R" 
    SUCCEED_RSP     = "!S"
    FAILURE_RSP     = "!F"
    EXECUTE_GET     = "!E"
    # response types
    STDOUTP         = "S"
    INCFILE         = "I"
    FILETRN         = "F"
    # filestream codes
    FILENAME    = "!N"
    FILETRAN    = "!T"
    FILESIZE    = "!Z"


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
            self.SERVERS.append(hostname)
            host, port = hostname.split(":")
            self.ADDRS.append((host, int(port)))

    def connect_to_socket(self, ADDR, blocking=0):
        SERVER = f"{ADDR[0]}:{ADDR[1]}" # check that addr[1] actually works
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(blocking)

        #self.SOCKETS[SERVER] = sock
        sock.connect_ex(ADDR)
        print(f"[socket]  Opened and connected to socket at {SERVER}.")
        return sock

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
            except Exception as e:
                print(f"Exception occurred while sending required files: {e}")
                exit()
        elif type == Codes.REQUEST_MSG:
            try:
                socket.sendall(type.encode(Comms.FORMAT))
                self.send_filestream(socket, val)
            except Exception as e:
                print(f"Exception occurred while sending required files: {e}")
                exit()
        elif type == Codes.DISCONN_MSG:
            try:
                socket.sendall(type.encode(Comms.FORMAT))
            except Exception as e:
                print(f"Exception occurred while attempting to disconnect: {e}")
                exit()
        elif type == Codes.FILENAME:
            try:
                socket.sendall(type.encode(Comms.FORMAT))
            except Exception as e:
                print(f"Exception occurred while requesting filename: {e}")
                exit()
        elif type == Codes.FILETRAN:
            try:
                socket.sendall(type.encode(Comms.FORMAT))
            except Exception as e:
                print(f"Exception occurred while requesting file transfer: {e}")
                exit()

    def send_command(self, socket, msg, addr):
        message = msg.encode(Comms.FORMAT) # b'echo hello cormac'
        msg_length = len(message)  # int:17
        send_length = str(msg_length).encode(Comms.FORMAT) # b'17'
        send_length += b' ' * (Comms.HEADER - len(send_length)) 
        # server: msg_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
        socket.sendall(send_length)
        #server: msg = conn.recv(msg_length).decode(Comms.FORMAT)
        socket.sendall(message)

    def handle_response(self, socket, filestream = False):
        header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
        code = header[0:2]
        response_flags = header[2:5]
        print(header)

        if code == Codes.EXECUTE_GET:
            length = int(header[2:-1])
            return int(socket.recv(length).decode(Comms.FORMAT))

        elif code == Codes.SUCCEED_RSP:
            length = int(header[5:-1])

            if filestream:
                filestream_flag = response_flags[0:2]
                if filestream_flag == Codes.FILENAME:
                    filename = socket.recv(length).decode(Comms.FORMAT)
                    return filename

            if response_flags[0] == Codes.STDOUTP:
                stdout = socket.recv(length).decode(Comms.FORMAT)
                print(stdout)

                if response_flags[1] == Codes.INCFILE:
                    self.receive_filestream(socket)

        elif code == Codes.FAILURE_RSP:
            length = int(header[2:-1])
            print("Server failed to execute:")
            print(socket.recv(length).decode(Comms.FORMAT))
            exit()

    def receive_filestream(self, socket):
        # filestreams are blocking
        socket.setblocking(1)
        # metadata packet
        header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
        code = header[0:2]
        response_flags = header[2:5]
        files_to_receive = int(header[5:-1])
        # receive the files
        while files_to_receive > 0:
            # get filename
            self.send(socket, Codes.FILENAME, "", "")
            filename = self.handle_response(socket, True)
            # get file
            self.send(socket, Codes.FILETRAN, "", "")
            # receive data and write to file https://www.thepythoncode.com/article/send-receive-files-using-sockets-python
            with open(filename, "wb") as f:
                while True:
                    data = socket.recv(Comms.MAX_LEN)
                    if not data:    
                        break
                    f.write(data)
            files_to_receive -= 1 
        socket.setblocking(0)

    def send_filestream(self, socket, files):
        print(f"sending filestream of {files}")
        print(os.getcwd())
        #sockets are blocking
        socket.setblocking(1)
        #send filestream packet
        code = Codes.SUCCEED_RSP
        response_type = Codes.STDOUTP + Codes.INCFILE + Codes.FILETRN
        files_to_send = str(len(files))
        padding = " " * (int(Comms.HEADER) - len(code) - len(response_type) - len(files_to_send))
        filestream_packet = str( code + response_type + files_to_send + padding)
        socket.sendall(filestream_packet.encode(Comms.FORMAT))

        for file in files:
            for i in range(3):
                # wait for filename request
                header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
                filestream_code = header[0:2]

                if filestream_code == Codes.FILENAME:
                    # send filename
                    filestream_code = Codes.FILENAME
                    filename_length = str(len(file))
                    padding = " " * (int(Comms.HEADER) - len(code) - len(filestream_code) - len(filename_length))
                    filename_packet = str(code + filestream_code + filename_length + padding + file)
                    socket.sendall(filename_packet.encode(Comms.FORMAT))

                if filestream_code == Codes.FILESIZE:
                    # send filesize
                    filestream_code = Codes.FILESIZE
                    filesize = str(os.path.getsize(file))
                    filesize_len = str(len(filesize))
                    padding = " " * (int(Comms.HEADER) - len(code) - len(filestream_code) - len(filesize_len))
                    filesize_packet = str(code + filestream_code + str(len(filesize)) + padding + filesize)
                    socket.sendall(filesize_packet.encode(Comms.FORMAT))

                if filestream_code == Codes.FILETRAN:
                    # send file https://www.thepythoncode.com/article/send-receive-files-using-sockets-python
                    with open(file, "rb") as f:
                        while True:
                            data = f.read(Comms.MAX_LEN)
                            if not data:
                                break
                            socket.sendall(data)
                            
        socket.setblocking(0)

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

    print(client.ADDRS)
    ready = client.ADDRS
    watchlist = []
    for actionset in client.ACTIONSETS: 
        commands_sent = 0
        for msg in actionset:
            location, command, required = msg[0], msg[1], msg[2]

            if location == "remote":
                # poll for cost
                lowestCost = 0
                lowestCostIndex = 0
                for i, server in enumerate(ready):
                    sock = client.connect_to_socket(server, 1)
                    client.send(sock, Codes.EXECUTE_GET, server, "")
                    exec_cost = int(client.handle_response(sock, server))
                    if exec_cost <= lowestCost:
                        lowestCostIndex = i
                        lowestCost = exec_cost
                    client.send(sock, Codes.DISCONN_MSG, server, "")
                sock = client.connect_to_socket(ready[lowestCostIndex])
            else:
                sock = client.connect_to_socket(("localhost", int(rakefileData.port)))

            # send requirements (if any)
            print(f"requirements required: {required}")
            if required != []:
                client.send(sock, Codes.REQUEST_MSG, "", required)

            # send command
            client.send(sock, Codes.COMMAND_MSG, "", command)
            watchlist.append(sock)
            commands_sent += 1

        while True:
            readable = select.select(watchlist, [], [])[0]
            if readable != []:
                for sock in readable:
                    client.handle_response(sock)
                    watchlist.remove(sock)
                    client.send(sock, Codes.DISCONN_MSG, "", "")
                    commands_sent -= 1

            if commands_sent == 0:
                break




    
    
  