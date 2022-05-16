import os
import socket
import threading
import sys
import subprocess
import errno

class Comms:
    HEADER = 64
    FORMAT = 'utf-8'

class Codes:
    DISCONN_MSG     = "!D"
    COMMAND_MSG     = "!C"
    REQUEST_MSG     = "!R"
    SUCCEED_RSP     = "!S"
    FAILURE_RSP     = "!F"

class Server:
    def __init__(self, host, port):
        self.HOST, self.PORT, self.SERVER = host, int(port), f"{host}:{port}"
        self.ADDR = (host, int(port))
        self.DIRPATH    = create_dir(os.getcwd()) 

        self.clients = list()
        self.dirs = dict()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[server]  Initialised rakeserver instance.")

        self.server.bind(self.ADDR)
        self.listen_to_socket()

    def listen_to_socket(self):
        self.server.listen()
        print(f"[r.s] listening on: {self.SERVER}")
        
        while True:
            conn, addr = self.server.accept() # blocks til connected
            new_client = get_hostname(addr)
            self.clients.append(new_client)
            self.dirs[new_client] = create_dir(f"{new_client}_tmp")
            
            thread = threading.Thread(target=self.manage_connection, args=(conn, addr))
            thread.start()
            print(f"(active: {threading.activeCount() - 1})\n")

    def manage_connection(self, conn, addr):
        print(f"NEW: {get_hostname(addr)}")
        connected = True

        try:
            while connected:
                msg_type = conn.recv(2).decode(Comms.FORMAT) 
                if msg_type == Codes.DISCONN_MSG:
                    connected = False
                # Received servable request.
                else:
                    msg_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
                    msg_length = int(msg_length)

                    if msg_type == Codes.COMMAND_MSG:
                        msg = conn.recv(msg_length).decode(Comms.FORMAT) 
                        try:
                            self.execute_command(msg, addr)
                            conn.send(Codes.SUCCEED_RSP.encode(Comms.FORMAT))
                        except:
                            conn.send(Codes.FAILURE_RSP.encode(Comms.FORMAT))
                            connected = False


                    elif msg_type == Codes.REQUEST_MSG:
                        name_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
                        name_length = int(name_length)
                        name = conn.recv(name_length).decode(Comms.FORMAT) 
                        msg = conn.recv(msg_length).decode(Comms.FORMAT) 
                        try:
                            self.get_requirement(name, msg, conn, addr)
                            conn.send(Codes.SUCCEED_RSP.encode(Comms.FORMAT))
                        except:
                            conn.send(Codes.FAILURE_RSP.encode(Comms.FORMAT))
                            connected = False
            self.disconnect_client(conn, addr)
        except KeyboardInterrupt:
            print("[r.s]  Transmission halted by user. ")
        finally:
            conn.close()

    def get_requirement(self, name, msg, conn, addr):
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

        try:
            file = os.open(name, flags)
        except OSError as error:
            if error.errno == errno.EEXIST:
                pass
            else: 
                conn.send(Codes.FAILURE_RSP.encode(Comms.FORMAT))
                raise
        else:
            with open(file, 'w') as file:
                file.write(msg)
            conn.send(Codes.SUCCEED_RSP.encode(Comms.FORMAT))

    def execute_command(self, msg, addr):
        message = msg.split()
        print(f"[{addr[0]}:{str(addr[1])}]:\n")
        with subprocess.Popen(message, stdout=subprocess.PIPE) as proc:
            print("> "+proc.stdout.read().decode(Comms.FORMAT))

    def disconnect_client(self, conn, addr):
        conn.close()
        self.clients.remove(get_hostname(addr))
        self.dirs.pop(get_hostname(addr))

def get_hostname(addr):
    return f"{addr[0]}:{str(addr[1])}"

def create_dir(dirName):
    print("[mkdir]  Creating '" + dirName+ "' in CD.")
    try: 
        os.mkdir(dirName)
        print("[mkdir]  Successfully created directory.")
    except FileExistsError:  # Thrown where dir exists
        print("[mkdir]  Directory already exists.")
    except: # Any other errors must halt execution 
        print("[mkdir]   ERROR: Cannot access or create directory.")
        exit()
    return os.getcwd() + "/" + dirName 


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("[r.s]\tArgument error; usage <host> <port>")
        sys.exit(1)

    # Uses Parser object to populate client data.
    server   = Server(sys.argv[1], sys.argv[2])


  


