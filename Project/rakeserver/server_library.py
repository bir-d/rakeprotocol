import os 
import selectors
import socket
import threading

# TODO: DESIGN NEW HEADER
HEADER     = 64        
FORMAT     = 'utf-8'

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

# Server objects manage execution/handling of client requests. 
class Server:
    def __init__(self, host, port, v=True):
        if v:print(" |-> [server]  Initialised rakeserver instance.")
        self.v          = v
        self.HOST, self.PORT, self.SERVER = host, int(port), f"{host}:{port}"
        self.ADDR = (host, int(port))
        self.DIRPATH    = create_dir(os.getcwd() + "/" + self.SERVER+"_tmp") 
        
    def open_socket(self):
        if self.v:print(f" |-> [socket]  Opening and binding socket at {self.ADDR}.")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(self.ADDR)
        self.listen_to_socket()

    def listen_to_socket(self):
        self.sock.listen()    
        print(f" |-> [socket]  Server is now listening on '{self.ADDR}'!")
        while True:
            conn, addr = self.sock.accept()
            thread = threading.Thread(target=self.manage_connection, args=(conn, addr))
            thread.start()

            print(f"ACTIVE: {threading.activeCount() - 1}\n")

    def manage_connection(self, conn, addr):
        print(f" |-> [connect]  Connected to {addr}")
        connected = True
        try:
            while connected:
                msg_length = conn.recv(HEADER).decode(FORMAT) #  need protocol header
                if msg_length:
                    msg_length = int(msg_length)
                    msg        = conn.recv(msg_length).decode(FORMAT)
                    print(f"{addr[0]}:{addr[1]}: '{msg}'")
                    # if msg == DISCONNECT_MESSAGE:
                        # connected = False
                    # else:
                        # execute_command(msg)
                    conn.send(f" |-> [{addr}]  Message recieved.".encode(FORMAT))
            conn.close()
        except KeyboardInterrupt:
            print(" |-> [socket]  Transmission halted by user. ")
        finally:
            conn.close()
        

if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'server.py'; file 'server_library.py' is a module only.")
  exit()
  