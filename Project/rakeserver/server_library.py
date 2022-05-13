from imp import new_module
import os
import select
import sys
import socket
import threading


# TODO: DESIGN NEW HEADER
HEADER     = 64        
FORMAT     = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"


def create_dir(dirName, v=True):
    if v:print(" |-> [mkdir]  Creating '" + dirName + "' in CD.")
    try: 
        os.mkdir(dirName)
        if v:print(" |-> [mkdir]  Successfully created directory.")
    except FileExistsError:  # Thrown where dir exists
        if v:print(" |-> [mkdir]  Directory already exists.")
    except: # Any other errors must halt execution 
        print(" |-> [mkdir]   ERROR: Cannot access or create directory.")
        exit()
    return os.getcwd() + "/" + dirName 


class Message:
    def __init__(self, event, message, value):
        self.event = event
        self.message = message
        self.requires = ""
        self.msg_len = sys.getsizeof(message)
        self.value = value
# Server objects manage execution/handling of client requests. 
class Server:
    def __init__(self, host, port):
        print(" |-> [server]  Initialised rakeserver instance.")
        self.HOST, self.PORT, self.SERVER = host, int(port), f"{host}:{port}"
        self.ADDR = (host, int(port))
        self.DIRPATH    = create_dir(self.SERVER+"_tmp") 
        self.sock_queue = list()

    def receive_header(self, sock):
        print("> Receiving header.")
        try:
            msg = sock.recv(64)
            # msg = msg.decode("utf-8")
            msg_size = len(msg)
            msg = msg.decode("utf-8").rstrip()
            msg_len = msg
            print(f"[Done] (header={msg_size} len={msg_len})")
        except: 
            print("> Could not receive header size.")
            return False, 0
        return True, msg_len
        
    def receive_message(self, socket, bytes):
        print("> Receiving message.")
        try: 
            message = socket.recv(bytes)        # reads all message, but will change
            message = message.decode("utf-8")

            msg_len = len(message)
            print("[Done]")
            # print(f"\t> {message} ({msg_len})")
        except:
            print("> No more messages to be received.")
            return False, "", 0
    
        return True, message, msg_len

    def process_message(self, sock, bytes, message):
        print("> Processing message.")
        connected = True
        if bytes == 0:
            print("> Found zero bytes.")
            if message != "":
                print("> Decoding.")
                decoded = message.decode("utf-8")
                if decoded:
                    if DISCONNECT_MESSAGE in decoded:
                        print("> Disconnecting from socket.")
                        connected = False
                    else:
                        print(f"> Message: {decoded}")
                        connected = True
                message = ""
                bytes = 0
        else:
            connected, new_msg, bytes_remaining = self.receive_message(sock, bytes)
            if connected:
                print("> Adding to message.")
                print(f"\t'{message}' += '{new_msg}'")
                message += new_msg
                bytes -= bytes_remaining
            else: 
                print("> Message read completed.")
                message = ""
                bytes = 0
        return connected, bytes, message

    def handle_client(self, socket):
        print("> Handling client.")
        msg = ""
        connected, bytes = self.receive_header(socket)
        
        if connected:
            while True:
                connected, bytes, message = self.process_message(socket, bytes, msg)
                msg += message
                if bytes == 0 or not connected:
                    break
            if connected and bytes == 0 and message != "":
                connected, bytes, message = self.process_message(socket, bytes, message)
                if bytes != 0 and message != "":
                    print("> Error printing message!")

        return connected

    def send_message(self, sock, message):
        msg = message.encode(FORMAT)
        msg_len = len(msg)
        send_len = str(len(message)).encode("utf-8")
        send_len += b' ' * (HEADER - len(send_len))
        # sock.send(send_len)
        sock.send(msg)

        return len(send_len), msg_len

    def return_message(self):
        connected = True
        message = "DATA RECEIVED SUCCESSFULLY"
        
        return connected, message


    def nonblock_service(self, sock, addr):
        print("> Servicing connections.")
        msg_queue = dict()
        writable = list()
        connected = True
        server_online = True

        while self.sock_queue and server_online:
            s_read, s_write, s_error = select.select(self.sock_queue, writable, self.sock_queue, 1)
            # handle reading of client data from sockets
            for sock in s_read:
                if sock == self.SERVER: # server has no queued commands
                    print("> Waiting for client...")
                    try:
                        conn, addr = sock.accept() 
                        conn.setblocking(False)
                        self.sock_queue.append(conn)
                        msg_queue[conn] = list()
                        print(f"> Connected to client at {(addr)}")
                    except: # sets server to check for client again
                        server_online = True
                else:
                    connected = self.handle_client(sock)
                    if connected:
                        if sock not in writable:
                            print("> Writing to socket")
                            writable.append(sock)
                            connected, updated_msg = self.update_message()
                            msg_queue[sock].append(updated_msg)
                    else:
                        self.sock_queue.remove(sock)
                        msg_queue.pop(sock)
                        if sock in writable:
                            writable.remove(sock)
                        writable.append(sock)
                        # sock.close()
                        print(f"> Disconnected from socket.")
            
            # handle the writing to socket for client to read
            for sock in s_write:
                print("\n[s_write]")
                if len(msg_queue) != 0:
                    msg = msg_queue[sock]
                    self.send_message(sock, msg)
                else:
                    writable.remove(sock)

            # handle the result of errors 
            for sock in s_error:
                self.sock_queue.remove(sock)
                msg_queue.pop(sock)
                if sock in writable:
                    writable.remove(sock)
                sock.close()
                print(f"> Disconnected from {sock.getsockname()}")

    def nonblocking_start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # prevent OSError
        sock.bind((self.HOST, self.PORT))
        sock.listen()
        self.SERVER = sock
        self.sock_queue.append(sock)
        
        try:
            self.nonblock_service(sock, (self.HOST, self.PORT))
        except (KeyboardInterrupt, SystemExit):
            sock.close()
            print("Keyboard Interrupt " )
        except:
            print("Failed to service.")
            sys.exit(-1)
        sock.close()

        
    '''VERSION B'''
    # def open_socket(self):
    #     print(f" |-> [socket]  Opening and binding socket at {self.ADDR}.")
    #     self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     # self.sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     self.sock.bind(self.ADDR)
    #     self.listen_to_socket()

    
    # # TODO: Handle busy server moments with threads
    # #       - Are threads 'self' or no?
    # #       - What happens on another connection attempt?
    # def listen_to_socket(self):
    #     self.sock.listen()    
    #     # self.sock.setblocking(False)
    #     # self.select.register(self.sock, selectors.EVENT_READ, data=None)
    #     print(f" |-> [socket]  Server is now listening on '{self.ADDR}'!")
    #     while True:
    #         # conn is socket, addr is host(ip:port)
    #         conn, addr = self.sock.accept() # blocks til connected
    #         # conn.setblocking(False)
    #         # send socket and host to handle_client()
    #         thread = threading.Thread(target=self.service_connection, args=(conn, addr))
    #         thread.start()

    #         print(f"ACTIVE: {threading.activeCount() - 1}\n")

    # def service_connection(self, conn, addr):
    #     print(f" |-> [connect]  Connected to {addr}")
    #     connected = True
    #     try:
    #         while connected:
    #             # events = self.sel.select(timeout=None)
    #             # for key, mask in events:
    #             #   if key.data is None:
    #             #       self.acceptConnection(key.fileobj)
    #             #   else:
    #             #       transmission = key.data
    #             #       try:
    #             #           transmission.process_events(mask)
    #             #       except Exception:
    #             #           print(" |-> [socket]  Error: An exception was thrown.")
    #             #           transmission.close()
    #             ''' blocks til receive msg from client'''
    #             msg_length = conn.recv(HEADER).decode(FORMAT) #  need protocol header
    #             if msg_length:
    #                 msg_length = int(msg_length)
    #                 msg        = conn.recv(msg_length).decode(FORMAT)
    #                 if msg == DISCONNECT_MESSAGE:
    #                     connected = False
    #                 print(f" |<- [service]  Disconnecting from '{addr[0]}:{addr[1]}'.")

    #                 conn.send(f" |<-  Server confirms message received ({addr[0]}:{addr[1]}).".encode(FORMAT))
    #         conn.close()
    #     except KeyboardInterrupt:
    #         print(" |-> [socket]  Transmission halted by user. ")
    #     finally:
    #         conn.close()
        

if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'server.py'; file 'server_library.py' is a module only.")
  exit()
  