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
    # filestream codes
    FILENAME    = "!N"
    FILETRAN    = "!T"

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
                print(msg_type)
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
                elif msg_type == Codes.REQUEST_MSG:
                    try:
                        self.receive_filestream(conn)
                    except:
                        connected = False
                else:
                    # client: socket.sendall(send_length)
                    msg_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
                    msg_length = int(msg_length) 

                    if msg_type == Codes.COMMAND_MSG:
                        # client: socket.sendall(message)
                        msg = conn.recv(msg_length).decode(Comms.FORMAT) 
                        self.execute_command(msg, addr, conn)
                        print(f"[{get_hostname(addr)}] Completed execution.")
            self.disconnect_client(addr)
        except KeyboardInterrupt:
            print("[r.s]  Transmission halted by user. ")
        except IOError as e:
            print(e)
            raise
        finally:
            conn.close()

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

    def receive_filestream(self, socket):
        print("receiving filestream")
        # filestreams are blocking
        socket.setblocking(1)
        # metadata packet
        header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
        code = header[0:2]
        response_flags = header[2:5]
        files_to_receive = int(header[5:-1])
        print(header, files_to_receive)
        # receive the files
        print(files_to_receive > 0)
        while files_to_receive > 0:
            # get filename
            print("getting filename")
            socket.sendall(Codes.FILENAME.encode(Comms.FORMAT))
            print("sent filename req")
            #have to manually get the header since we dont have handle_connection()
            header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
            code = header[0:2]
            filestream_code = header[2:5]
            length = int( header[5:-1] )
            filename = socket.recv(length).decode(Comms.FORMAT)
            print(header, filename)


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
            # wait for filename request
            header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
            code = header[0:2]
            response_flags = header[2:5]
            filestream_code = response_flags[0:2]
            if filestream_code == Codes.FILENAME:
                # send filename
                filestream_code = Codes.FILENAME
                filename_length = str(len(file))
                padding = " " * (int(Comms.HEADER) - len(code) - len(filestream_code) - len(filename_length))
                filename_packet = str(code + filestream_code + filename_length + padding)
                socket.sendall(filename_packet.encode(Comms.FORMAT))
            elif filestream_code == Codes.FILETRAN:
                # send file https://www.thepythoncode.com/article/send-receive-files-using-sockets-python
                with open(file, "rb") as f:
                    while True:
                        data = f.read(Comms.MAX_LEN)
                        if not data:
                            break
                        socket.sendall(data)
        socket.setblocking(0)

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


  


