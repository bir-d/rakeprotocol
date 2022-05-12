import os 
import selectors
import socket

# Server objects manage execution/handling of client requests. 
class Server:
    def __init__(self, host, port, v=True):
        if v:print(" |-> [server]  Initialised rake server.")
        self.host       = host
        self.port       = int(port)
        if v:print(" |-> [server]  Server data structures populated successfully.")

    def addSocket(self, SocketObject):
        self.socket = SocketObject

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
        self.select = select
        self.sock = sock
        self.address = address
        self._recv_buffer = b""
        self._send_buffer = b""
        self.request = None
        self.response_created = False

# Used for management of socket functionality.
class SocketHandling:
    # Create a socket to communicate to server.
    def __init__(self, host, port):
        print(" |-> [socket]  Creating socket for '" + host+":" + str(port) + "'.")
        self.host, self.port = host, port
        self.select = selectors.DefaultSelector()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(" |-> [socket]  Successfully created socket.\n |")

    
    # Enable listening to the socket for communication.
    def initiateListening(self):
        print(" |-> [socket]  Enabling socket listening.")
        self.sock.bind((self.host, self.port))
        self.sock.listen()    
        self.sock.setblocking(False)
        self.select.register(self.sock, selectors.EVENT_READ, data=None)

        print(" |-> [socket]  Listening on '" + self.host + ":" + str(self.port) + "' enabled!")

    def acceptConnection(self, sock):
        connection, address = sock.accept()  
        connection.setblocking(False)
        
        print(" |-> [socket]  Accepted connection from '" +address[0] + str(address[1]) + "'.")

        transmission = DataTransmission(self.select, connection, address)
        print(" |-> [socket]  Prepared data structure.")

        self.select.register(connection, selectors.EVENT_READ, data=transmission)

    def awaitClient(self):
        print(" |-> [socket]  Awaiting client connection...")
        try:
            while True:
                events = self.select.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.acceptConnection(key.fileobj)
                    else:
                        transmission = key.data
                        try:
                            transmission.process_events(mask)
                        except Exception:
                            print(" |-> [socket]  Error: An exception was thrown.")
                            transmission.close()

        except KeyboardInterrupt:
            print(" |-> [socket]  Transmission halted by user. ")
        finally:
            self.select.close()


if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'server.py'; file 'server_library.py' is a module only.")
  exit()
  