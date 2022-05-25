import os
import socket
import threading
import sys
import subprocess
import shutil

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
    FILESIZE    = "!Z"

class Server:
    def __init__(self, host, port, v=False):
        self.HOST, self.PORT, self.SERVER = host, int(port), f"{host}:{port}"
        self.ADDR       = (host, int(port))
        self.DIRPATH    = os.path.abspath(os.getcwd()) 

        self.v = v
        self.clients = list()
        self.dirs = dict()  # dirs[CLIENTHOST] = directory/path/of/client/files 
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("[server]  Initialised rakeserver instance.\n")

        self.server.bind(self.ADDR)
        self.listen_to_socket()

    def listen_to_socket(self):
        self.server.listen()
        print(f"[r.s] listening on: {self.SERVER}")
        
        while True: # TODO: Look into how to send back more than just stdout to client
            conn, addr = self.server.accept() # blocks til connected
            new_client = get_hostname_from_socket(conn) 
            self.clients.append(new_client)
            os.chdir(self.DIRPATH)
            os.mkdir(new_client)
            clientpath = os.path.join(self.DIRPATH, new_client)
            self.dirs[new_client] = os.path.abspath(clientpath)
            
            thread = threading.Thread(target=self.manage_connection, args=(conn, addr))
            thread.start()
            if self.v: print(f"(active: {threading.activeCount() - 1})\n")

    def manage_connection(self, conn, addr):
        if self.v: print(f"NEW: {get_hostname_from_socket(conn)}")
        connected = True
        required = []
        try:
            while connected:
                header = conn.recv(Comms.HEADER).decode(Comms.FORMAT)
                msg_type = header[0:2]
                if self.v: print(msg_type)
                if msg_type == Codes.DISCONN_MSG:
                    # Should be empty anyways, so meaningless name
                    if self.v: print(f"[{get_hostname(addr)}]\tDisconnecting from client.\n")
                    connected = False
                elif msg_type == Codes.EXECUTE_GET:
                    # Should be empty anyways, so meaningless name
                    if self.v: print(f"[{get_hostname(addr)}]\tSending execution cost.\n")
                    code = Codes.EXECUTE_GET
                    cost = str(threading.active_count() - 1)
                    payload_length = str(len(cost))
                    padding = " " * (int(Comms.HEADER) - len(code) - len(payload_length))
                    header = str(code + payload_length + padding)
                    conn.sendall(header.encode(Comms.FORMAT))
                    conn.sendall(cost.encode(Comms.FORMAT))
                elif msg_type == Codes.REQUEST_MSG:
                    # Should be empty anyways, so meaningless name
                    try:
                        required = self.receive_filestream(conn, True)
                    except:
                        connected = False
                else:
                    if msg_type == Codes.COMMAND_MSG:
                    # client: socket.sendall(send_length)
                        length = int(header[2:-1])
                        # client: socket.sendall(message)
                        msg = conn.recv(length).decode(Comms.FORMAT) 
                        self.execute_command(msg, addr, conn, required)
                        if self.v: print(f"[{get_hostname(addr)}] Completed execution.\n")
            self.disconnect_client(addr)
        except KeyboardInterrupt:
            print("[r.s]  Transmission halted by user. ")
        except IOError as e:
            print(e)
            raise
        finally:
            conn.close()


    def execute_command(self, msg, addr, conn, required = []):
        os.chdir(get_socket_dir(conn, self.dirs))
        if self.v: print(f"EXECUTING COMMAND {msg} IN DIRECTORY {os.getcwd()} FOR {get_hostname_from_socket(conn)}")
        if self.v: print(f"[{addr[0]}:{str(addr[1])}]: > {msg}")
        message = msg.split()
        generated_files = []
        # TODO: error handling
        try:
            print(f"\n[command@{get_hostname(addr)}] > {msg}")
            with subprocess.Popen(message, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=get_socket_dir(conn, self.dirs)) as proc:
                stdout, stderr = proc.communicate()
                if isinstance(stdout, bytes):
                    stdout = stdout.decode(Comms.FORMAT)
                    if len(stdout) != 0:
                        print(f"[command@{get_hostname(addr)}] > stdout: "+ stdout)
                    else:
                        if self.v: print(f"[command@{get_hostname(addr)}] > No stdout to report.")

                if isinstance(stderr, bytes):
                    stderr = stderr.decode(Comms.FORMAT)
                    if len(stderr) != 0:
                        print(f"[command@{get_hostname(addr)}] > stderr: "+ stderr)
                    else:
                        if self.v: print(f"[command@{get_hostname(addr)}] > No stderr to report.")

                exit_code = proc.returncode
                if self.v: print(f"[command@{get_hostname(addr)}] > return code: {exit_code}")
            
            if exit_code == 0:
                code = Codes.SUCCEED_RSP
                
                # Check for generated files by comparing directory contents with files received for requirements
                directory_contents = os.listdir(get_socket_dir(conn, self.dirs))
                for file in directory_contents:
                    if file not in required:
                        generated_files.append(get_socket_dir(conn, self.dirs) + file)
                        if self.v: print(f"[command@{get_hostname(addr)}] > Generated file detected: {file}")
                # Set incfile flag based on if generated files were detected
                if generated_files != []:
                    options = Codes.STDOUTP + Codes.INCFILE + " "
                else:
                    options = Codes.STDOUTP + " " + " "
                # Send packet to client
                msg_len = str(len(stdout))
                padding = (' ' * (Comms.HEADER - len(code) - len(options) - len(msg_len)))
                header = (code + options + msg_len + padding).encode(Comms.FORMAT)
                conn.sendall(header)
                conn.sendall(stdout.encode(Comms.FORMAT))

                # We need to send generated files, if they exist
                if generated_files != []:
                    self.send_filestream(conn, generated_files)

            elif exit_code != 0:
                code = Codes.FAILURE_RSP
                payloads = (stderr, str(exit_code))
                for payload in payloads:
                    payload_length = str(len(payload))
                    padding = " " * (int(Comms.HEADER) - len(code) - len(payload_length))
                    header = str(code + payload_length + padding).encode(Comms.FORMAT)
                    conn.sendall(header)
                    conn.sendall(payload.encode(Comms.FORMAT))

        except Exception as e:
            print(e)

    def disconnect_client(self, addr):
        self.clients.remove(get_hostname(addr))
        if self.v: print(f"CLEANING UP {get_hostname(addr)}")
        shutil.rmtree(self.dirs[get_hostname(addr)], ignore_errors=True)
        self.dirs.pop(get_hostname(addr))

    # citation: https://stackoverflow.com/a/17668009
    def recvall(self, sock, n):
        if self.v: print(f"receiving {n} bytes from socket")
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def receive_filestream(self, socket, return_received = False):
        os.chdir(self.dirs[get_hostname_from_socket(socket)])
        if self.v: print(f"[filestream]\treceiving filestream from {get_hostname_from_socket(socket)}. I am in {os.getcwd()}")
        received_files = []
        # metadata packet
        header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
        code = header[0:2]
        response_flags = header[2:5]
        files_to_receive = int(header[5:-1])
        # receive the files
        while files_to_receive > 0:
            if self.v: print(f"[filestream]\t{files_to_receive} files to receive")
            # get filename
            if self.v: print("[filestream]\tgetting filename")
            socket.sendall(Codes.FILENAME.encode(Comms.FORMAT))
            if self.v: print("[filestream]\tsent filename req")

            #have to manually get the packet since we dont have handle_connection()
            header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
            code = header[0:2]
            filestream_code = header[2:5]
            length = int( header[5:-1] )
            filename = socket.recv(length).decode(Comms.FORMAT)
            if self.v: print(f"[filestream]\tfilename: {filename}")

            # get filesize
            socket.sendall(Codes.FILESIZE.encode(Comms.FORMAT))
            header = socket.recv(Comms.HEADER).decode(Comms.FORMAT)
            code = header[0:2]
            filestream_code = header[2:5]
            length = int( header[5:-1] )
            filesize = int(socket.recv(length).decode(Comms.FORMAT))
            if self.v: print(f"[filestream]\tfilesize: {filesize}")

            # get file
            if self.v: print(f"[filestream]\tsending file transfer request for {filename}")
            socket.sendall(Codes.FILETRAN.encode(Comms.FORMAT))

            # receive data and write to file https://www.thepythoncode.com/article/send-receive-files-using-sockets-python
            with open(get_socket_dir(socket, self.dirs) + filename, "wb") as f:
                data = self.recvall(socket, filesize)
                f.write(data)
            f.close()
            if self.v: print("[filestream]\tfile received")

            received_files.append(filename)
            files_to_receive -= 1 
        if return_received:
            return received_files

    def send_filestream(self, socket, files):
        if self.v: print(f"[filestream]\tsending filestream of {files}")
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
                    filename = os.path.basename(file)
                    filestream_code = Codes.FILENAME + Codes.FILETRN
                    filename_length = str(len(filename))
                    padding = " " * (int(Comms.HEADER) - len(code) - len(filestream_code) - len(filename_length))
                    filename_packet = str(code + filestream_code + filename_length + padding + filename)
                    socket.sendall(filename_packet.encode(Comms.FORMAT))

                if filestream_code == Codes.FILESIZE:
                    # send filesize
                    filestream_code = Codes.FILESIZE + Codes.FILETRN
                    filesize = str(os.path.getsize(file))
                    filesize_len = str(len(filesize))
                    padding = " " * (int(Comms.HEADER) - len(code) - len(filestream_code) - len(filesize_len))
                    filesize_packet = str(code + filestream_code + str(len(filesize)) + padding + filesize)
                    socket.sendall(filesize_packet.encode(Comms.FORMAT))

                if filestream_code == Codes.FILETRAN:
                    # send file https://www.thepythoncode.com/article/send-receive-files-using-sockets-python
                    with open(file, "rb") as f:
                        data = f.read()
                        socket.sendall(data)


def get_hostname(addr):
    return f"{addr[0]}:{str(addr[1])}"

def get_hostname_from_socket(socket):
    peername = socket.getpeername()
    return f"{peername[0]}:{str(peername[1])}"

def get_socket_dir(socket, dirs):
    return dirs[get_hostname_from_socket(socket)] + "/"

# def create_dir(dirName, location):
#     print("[mkdir]  Creating '" + dirName+ "' in CD.")
#     try:
#         os.mkdir(dirName)
#         print("[mkdir]  Successfully created directory.")
#     except FileExistsError:  # Thrown where dir exists
#         print("[mkdir]  Directory already exists.")
#     except: # Any other errors must halt execution 
#         print("[mkdir]   ERROR: Cannot access or create directory.")
#         exit()
#     return os.getcwd() + "/" + dirName 


if __name__ == '__main__':
    try:
        v = sys.argv[3]
        print("[r.p]\tVerbose mode enabled.\n")
    except IndexError:
        v = False
        print("[r.p]\tVerbose mode disabled. Enable by passing either `1` or `True` as argv[3]\n")
    if len(sys.argv) < 3:
        print("[r.s]\tArgument error; usage <host> <port> [verbose]")
        sys.exit(1)

    # Create server object
    server   = Server(sys.argv[1], sys.argv[2], v)


  


