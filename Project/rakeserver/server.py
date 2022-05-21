import os
import socket
import threading
import sys
import subprocess
import errno

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
    # file codes
    STDOUTP         = "S"
    INCFILE         = "I"
    FILETRN         = "F"

class Server:
    def __init__(self, host, port):
        self.HOST, self.PORT, self.SERVER = host, int(port), f"{host}:{port}"
        self.ADDR       = (host, int(port))
        self.DIRPATH    = os.getcwd() 

        self.clients = list()
        self.dirs = dict()  # dirs[CLIENTHOST] = directory/path/of/client/files 
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[server]  Initialised rakeserver instance.")

        self.server.bind(self.ADDR)
        self.listen_to_socket()

    def listen_to_socket(self):
        self.server.listen()
        print(f"[r.s] listening on: {self.SERVER}")
        
        while True: # TODO: Look into how to send back more than just stdout to client
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
                    print(f"Disconnecting from client at '{get_hostname(addr)}'.")
                    connected = False
                elif msg_type == Codes.EXECUTE_GET:
                    print(f"Sending execution cost to '{get_hostname(addr)}'.")
                    cost = threading.active_count() - 1
                    cost = str(cost).encode(Comms.FORMAT)
                    send_len = str(len(cost)).encode(Comms.FORMAT)
                    send_len += b' ' * (Comms.HEADER - len(send_len))
                    conn.sendall(send_len)
                    conn.sendall(cost)
                else:
                    # client: socket.sendall(send_length)
                    msg_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
                    msg_length = int(msg_length) 

                    if msg_type == Codes.COMMAND_MSG:
                        # client: socket.sendall(message)
                        msg = conn.recv(msg_length).decode(Comms.FORMAT) 
                        self.execute_command(msg, addr, conn)
                        print(f"[{get_hostname(addr)}] Completed execution.")
                    elif msg_type == Codes.REQUEST_MSG:
                        name_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
                        name_length = int(name_length)
                        name = conn.recv(name_length).decode(Comms.FORMAT) 
                        msg = conn.recv(msg_length).decode(Comms.FORMAT) 
                        try:
                            self.get_requirement(name, msg, conn, addr)
                        except:
                            connected = False
            self.disconnect_client(addr)
        except KeyboardInterrupt:
            print("[r.s]  Transmission halted by user. ")
        except IOError as e:
            print(e)
            raise
        finally:
            conn.close()

    def get_requirement(self, name, msg, conn, addr):
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            os.chdir(self.dirs[get_hostname(addr)])
            file = os.open(name, flags)
        except OSError as error:
            if error.errno == errno.EEXIST:
                pass
            else: 
                # conn.send(Codes.FAILURE_RSP.encode(Comms.FORMAT))
                raise
        else:
            try:
                with open(file, 'w') as file:
                    file.write(msg)
                # conn.send(Codes.SUCCEED_RSP.encode(Comms.FORMAT))
            except IOError as e:
                if e.errno == errno.EPIPE:
                    pass
            else:
                os.chdir(self.DIRPATH)
            finally:
                os.chdir(self.DIRPATH)


    def execute_command(self, msg, addr, conn):
        print(f"[{addr[0]}:{str(addr[1])}]: > {msg}")
        message = msg.split()
        # TODO: manages pipe messages
        try:
            with subprocess.Popen(message, stdout=subprocess.PIPE) as proc:
                result = proc.stdout.read()
                print("stdout: "+ result.decode(Comms.FORMAT))

            code = Codes.SUCCEED_RSP
            options = "S  "
            msg_len = str(len(result))
            padding = (' ' * (Comms.HEADER - len(code) - len(options) - len(msg_len)))

            header = (code + options + msg_len + padding).encode(Comms.FORMAT)
            conn.sendall(header)
            conn.sendall(result)
        except Exception as e:
            print(e)

    def disconnect_client(self, addr):
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

    # Create server object
    server   = Server(sys.argv[1], sys.argv[2])


  


