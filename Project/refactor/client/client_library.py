from http import client, server
import os
import sys
import socket
import select
from xmlrpc.client import Server


HEADER_SIZE = 64
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT".encode(FORMAT)




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

        self.s_initiate_connection(self.ADDRS[0][0], self.ADDRS[0][1])

    def s_initiate_connection(self, host, port):
        print("Connecting...")
        sock = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
        connection = sock.connect_ex((host, port))

        if connection != 0:
            print("Failed to connect.")
            return 0

        message = "Init"
        self.s_send_message(sock, message)

        server_connected = self.s_handle_server(sock)

        client_input = ""

        while server_connected:
            client_input = input(">>")
            if "!DISCONNECT" in client_input:
                print("[DISCONNECT] Disconnecting...") 
                self.s_send_message(sock, DISCONNECT_MESSAGE)
                server_connected = False
            else:
                self.s_send_message(sock, client_input)
                server_connected = self.s_handle_server(sock)

    # Manages examination of client requests.
    def s_handle_server(self, socket):
        print("[S_HANDLE] Examining server socket for requests.")
        message = b""    # Stores the message as the request is examined.
        
        # Examine the socket for header for request metadata.
        server_connected, remaining_bytes = self.s_receive_header(socket) 
        
        # Server header was able to be read.
        if server_connected:
            while True:
                # Read message data after the header data.
                server_connected, remaining_bytes, message = self.s_process_message(socket, remaining_bytes, message)

                # Server has no more bytes to send, or has disconnected from the socket.
                if remaining_bytes == 0 or not server_connected:
                    break
            
            # Server has no bytes to send, remains connected, and the message received contains data.
            if server_connected and remaining_bytes == 0 and message != b"":
                # Continue to read message data.
                server_connected, remaining_bytes, message = self.s_process_message(socket, remaining_bytes, message)

                # Where bytes found or message received is empty, error has occurred.
                if remaining_bytes != 0 or message != b"":
                    print("[S_HANDLE] WARNING: Examine integrity of message as it appears damaged; continuing execution.")

        return server_connected

    # Listens and receives new messages sent, 
    def s_process_message(self, sock, message_size, message_data):
        print("[MSG_PROCESS] Processing message data.")
        server_connected = True
        remaining_bytes = message_size
        message = message_data 

        # Message has been completely processed.
        if message_size == 0:
            print("[MSG_PROCESS] Received message of length zero.")
            if message_data != b"":
                print("[MSG_PROCESS] Decoding message.")
                # Decode into readable format.
                decoded_message = message_data.decode("utf-8")   

                # Message exists and is not empty, examine it.
                if decoded_message:
                    if "!DISCONNECT" in decoded_message:
                        print("[MSG_PROCESS] Disconnecting from client socket.")
                        server_connected = False
                    else:
                        print(f"[MSG_PROCESS] Received message:\t> {decoded_message}")
                        server_connected = True
                message_data = b""
                remaining_bytes = 0

        else: # Message has remaining bytes to be read.
            server_connected, read_message, read_bytes = self.s_receive_message(sock, message_size)

            # As client still connected, append data read to the end of message received so far.
            if server_connected:
                print(f"[MSG_PROCESS] Adding to end of message.")
                print(f"\t'{message_data}' += '{read_message}'")
                message         += read_message
                remaining_bytes -= read_bytes
            else: 
                print("[MSG_PROCESS] Server disconnected.")
                print(f'\t> `{message}')
                message         = b""
                remaining_bytes = 0

        return server_connected, remaining_bytes, message


    def s_send_message(self, sock, message):
        send_message = message.encode(FORMAT)
        message_length = len(send_message)

        send_len = str(message_length).encode("utf-8")
        send_len += b' ' * (HEADER_SIZE - len(send_len))

        sock.send(send_len)
        sock.send(send_message)


    # Retrieve incoming message data.
    def s_receive_message(self, socket, size):
        print("[MSG_RECEIVE] Receiving message data.")
        message = b""
        read_bytes = 0
        client_connected = True

        try: 
            message = socket.recv(size)        # reads all message, but will change
            print(message)
            read_bytes = sys.getsizeof(message)
            # message = message.decode("utf-8")
        except:
            print("[MSG_RECEIVE] ERROR: Message receiving encountered an issue; disconnecting.")
            client_connected = False
    
        return client_connected, message, read_bytes

    # Examines the header information of a message.
    def s_receive_header(self, sock):
        print("[RECV_HEADER] Examining message header.")
        server_connected = True
        message_size = 0

        try: # Read in data of expected header size.
            message = sock.recv(HEADER_SIZE)
        except:
            server_connected = False
        
        if server_connected:
            try:
                message_size = sys.getsizeof(message)
            except: 
                print("[RECV_HEADER] ERROR: Failed to determine message size.")
                message_size = 0
                server_connected = False
            # message = message.decode("utf-8").rstrip()
            # msg_len = message
            print(f"[RECV_HEADER] Recieved message size = {message_size} bytes (expected {HEADER_SIZE}).") 

        return server_connected, message_size


    def s_return_message(self, socket):
        server_connected = True
        message = "DATA RECEIVED"

        try:
            self.s_send_message(socket, message)
        except:
            server_connected = False
            message = ""
            
        return server_connected, message


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

if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'client.py'; file 'client_library.py' is a module only.")
  exit()