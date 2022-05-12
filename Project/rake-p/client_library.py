import os
import socket
import selectors
import sys

# Client objects manage connections to servers in the Rakefile.
class Client: 
    def __init__(self, rakeData, v=True):
        if v:print(" |-> [client]  Initialised rake.p client.")
        self.port         = rakeData.port
        self.hosts        = rakeData.hosts
        self.actionsets   = rakeData.actionsets
        self.sockets      = dict()
        if v:print(" |-> [client]  Client data structures populated successfully.")

    def addSocket(self, host, SocketObject):
        self.sockets[host] = SocketObject

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

# Allows for client-relative dir functions.
class DirectoryNavigator:
    def __init__(self, hostPath):
        self.defaultPath = hostPath + "/"

    # Creates a directory in current working directory.
    def createDir(self, dirName):
        print(" |-> [dirNav]  Creating '" + dirName + "' in CD.")
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

# Handles header file sent to the server.
class Message:
    def __init__(self, select, sock, address, command):
        self.select = select
        self.sock = sock
        self.address = address
        self.command = command
        self._recv_buffer = b""
        self._send_buffer = b""
        self._command_queued = False
        self.response = None

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def write(self):
        if not self._command_queued:
            self.queue_command()

        '''_write()'''
        if self._send_buffer:
            print(f"Sending {self._send_buffer!r} to {self.address}")
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]

        if self._command_queued:
            if not self._send_buffer:
                # Set selector to listen for read events, we're done writing.
                self._set_selector_events_mask("r")

    def close(self):
        print(f"Closing connection to {self.address}")
        try:
            self.select.unregister(self.sock)
        except Exception as e:
            print(
                f"Error: selector.unregister() exception for "
                f"{self.address}: {e!r}"
            )
        try:
            self.sock.close()
        except OSError as e:
            print(f"Error: socket.close() exception for {self.address}: {e!r}")
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def queue_command(self):
        self._send_buffer += self.message
        self._command_queued = True

# Used for management of socket functionality.
class SocketHandling:
    # Create a socket to communicate to server.
    def __init__(self, host, port):
        print(" |-> [socket]  Connecting to '" + host+":" + str(port) + "'.")
        self.select = selectors.DefaultSelector()
        self.host, self.port = host, port

        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(" |-> [socket]  Successfully created socket.")

    def connect(self, command):
        address = (self.host, self.port)
        print(f"Starting connection to {address}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(address)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        message = Message(self.select, sock, address, command)
        self.select.register(sock, events, data=message)


    def awaitServer(self):
        print(" |-> [socket]  Waiting for server...")
        try:
            while True:
                events = self.select.select(timeout=1)
                for key, mask in events:
                    message = key.data
                    try:
                        message.process_events(mask)
                    except Exception as e:
                        print(" |-> [socket]  ERROR: An exception occurred.\n\n",e,"\n", sep="")
                        message.close()
                if not self.select.get_map():
                    break
        except KeyboardInterrupt:
            print(" |-> [socket]  Transmission halted by user. ")
        finally:
            self.select.close()

if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'client.py'; file 'client_library.py' is a module only.")
  exit()