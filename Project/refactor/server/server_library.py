from http import client
import os
import select
import sys
import socket

HEADER_SIZE     = 64        
FORMAT     = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT".encode(FORMAT)


# Server objects manage execution/handling of client requests. 
class Server:
    def __init__(self, host, port):
        print(" |-> [server]  Initialised rakeserver instance.")
        # Stores servers IP and port, and this combined as a string.
        self.HOST, self.PORT, self.HOSTNAME = host, int(port), f"{host}:{port}"

        # Tuple of IP and port as a number for socket services.
        self.ADDR = (host, int(port))

        # Stores the directory used for all socket data.
        self.DIRPATH    = create_dir(self.HOSTNAME+"_tmp") 

        # Holds sockets requiring service in order of request time.
        self.client_sock_queue = list()

        # Begins socket communication.
        self.s_initiate_connection()
        

    # Initialises the server's socket then performs services on connection.
    def s_initiate_connection(self):
        # Open IPv4 socket for TCP-type data stream.
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Prepares socket for reuse (prevents OSError).
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        sock.bind((self.HOST, self.PORT)) # Bind server to address.



        # Begins listening for requests.
        sock.listen()    

        # Adds own socket to the top of the queue (ready for clients).
        self.client_sock_queue.append(sock)

        # Stores the server's opened socket object.
        self.SERVER = sock

        try: # Attempt to service connection until ended by user or error.
            self.s_service_connection()
        except (KeyboardInterrupt, SystemExit): # User terminated server.
            print("[STOPPING] Received signal to terminate server." )
        except: # Errors halt server execution.
            print(f"\n[STOPPING] Server terminated.")
            sys.exit(-1)

        # Close the server's socket.
        sock.close()    

    # Handles the communication with clients on socket
    def s_service_connection(self):
        print("[SERVICE] Ready to accept client requests.")
        client_msg_queue    = dict()    # Messages to be sent to clients (client_socket, messages_list)
        writable_sockets    = list()    # Holds sockets ready to be written to.
        server_online       = True      # Server process is running.
        client_connected    = True      # Server is connected to the socket.

        # Operate server while online and connection requests exist.
        while self.client_sock_queue and server_online:
            # Monitors sockets of queued clients and write-ready sockets.
            s_read, s_write, s_error = select.select(self.client_sock_queue, 
                                                    writable_sockets, 
                                                    self.client_sock_queue, 1)

            for socket in s_read:
                if socket == self.SERVER: # Server socket seen at top of queue.
                    print("[S_READ] Awaiting client requests...")
                    try:    # Accept client `conn`ection socket `addr`ess to server socket. 
                        conn, addr = socket.accept() 
                        conn.setblocking(False)
                        print(f"[S_READ:'{(addr)}'] Connected to client.")

                        # Add client to queue of servicable sockets.
                        self.client_sock_queue.append(conn)

                        # Initiate the clients message request queue.
                        client_msg_queue[conn] = list()
                        print(f"[S_READ:'{(addr)}'] Added client to service queue.")
                    except: # No servicable clients; search for new client requests.
                        server_online = True

                else:  # Server has client with queued commands.
                    # Handles the client's requests on their socket.
                    client_connected = self.s_handle_client(socket)

                    # If still connected to the client; return a message to client.
                    if client_connected:
                        # Socket not already waiting to be written to.
                        if socket not in writable_sockets:
                            writable_sockets.append(socket) # Note socket is writable.
                            # Determine return message.
                            client_connected, return_message = self.s_return_message(socket)

                            # Add message to socket's queue of messages to send.
                            client_msg_queue[socket].append(return_message)
                    
                    # Handling of client resulted in a disconnection.
                    else: 
                        client_connected, return_message = self.s_return_message(socket)
                        # Remove the client from service queue.
                        self.client_sock_queue.remove(socket)
                        # Remove all messages prepared for sending to client.
                        client_msg_queue.pop(socket)

                        # Remove socket from queue of writable sockets.
                        if socket in writable_sockets:
                            writable_sockets.remove(socket)

                        # Disconnect the socket.
                        socket.close()
                        print(f"[S_READ] Disconnected from client.")
            
            # Examines sockets set for writing.
            for socket in s_write:
                # Server has message waiting to be sent to client.
                if len(client_msg_queue) != 0:  
                    print("[S_WRITE] Sending return message.")
                    # Message taken from top of the queue.
                    message = (client_msg_queue[socket]).pop(0)
                    # Send message to client via their connection socket.
                    self.s_send_message(socket, message)

                # Server has no messages to send; removes socket from writing queue.
                else:
                    print("[S_WRITE] No messages to return; removing from writing queue.")
                    writable_sockets.remove(socket)

            # Examines sockets that indicate an error/exception has occurred.
            for socket in s_error:
                # Remove socket from service queue.
                self.client_sock_queue.remove(socket)

                # Remove socket's return message queue.
                client_msg_queue.pop(socket)

                # Remove socket from list of writable sockets.
                if socket in writable_sockets:
                    writable_sockets.remove(socket)

                socket.close()
                print(f"[S_ERROR] Disconnected from socket due to error.")

    # Manages examination of client requests.
    def s_handle_client(self, socket):
        print("[S_HANDLE] Examining client socket for requests.")
        message = b""    # Stores the message as the request is examined.
        
        # Examine the socket for header for request metadata.
        client_connected, remaining_bytes = self.s_receive_header(socket) 
        
        # Client header was able to be read.
        if client_connected:
            while True:
                # Read message data after the header data.
                client_connected, remaining_bytes, message = self.s_process_message(socket, remaining_bytes, message)

                # message += recieved_message

                # Client has no more bytes to send, or has disconnected from the socket.
                if remaining_bytes == 0 or not client_connected:
                    break
            
            # Client has no bytes to send, remains connected, and the message received contains data.
            if client_connected and remaining_bytes == 0 and message != b"":
                # Continue to read message data.
                client_connected, remaining_bytes, message = self.s_process_message(socket, remaining_bytes, message)

                # Where bytes found or message received is empty, error has occurred.
                if remaining_bytes != 0 or message != b"":
                    print("[S_HANDLE] WARNING: Examine integrity of message as it appears damaged; continuing execution.")

        return client_connected


    # Examines the header information of a message.
    def s_receive_header(self, sock):
        print("[RECV_HEADER] Examining message header.")
        client_connected = True
        message_size = 0

        try: # Read in data of expected header size.
            message = sock.recv(HEADER_SIZE)
        except:
            client_connected = False
        
        if client_connected:
            try:
                message_size = sys.getsizeof(message)
            except: 
                print("[RECV_HEADER] ERROR: Failed to determine message size.")
                message_size = 0
                client_connected = False
            # message = message.decode("utf-8").rstrip()
            # msg_len = message
            print(f"[RECV_HEADER] Recieved message size = {message_size} bytes (expected {HEADER_SIZE}).") 

        return client_connected, message_size
        
    # Listens and receives new messages sent, 
    def s_process_message(self, sock, message_size, message_data):
        print("[MSG_PROCESS] Processing message data.")
        client_connected = True
        remaining_bytes = message_size
        message = message_data 

        # Message has been completely processed.
        if message_size == 0:
            print("[MSG_PROCESS] Completed message.")
            if message_data != b"":
                print("[MSG_PROCESS] Decoding message.")
                # Decode into readable format.
                decoded_message = message_data.decode("utf-8")   

                if DISCONNECT_MESSAGE in decoded_message:
                    print("[MSG_PROCESS] Disconnecting from client socket.")
                    client_connected = False
                else:
                    print(f"[MSG_PROCESS] Received message:\t> {decoded_message}")
                    client_connected = True
                message = ""
                remaining_bytes = 0
        else: # Message has remaining bytes to be read.
            client_connected, read_message, read_bytes = self.s_receive_message(sock, message_size)

            # As client still connected, append data read to the end of message received so far.
            if client_connected:
                print(f"[MSG_PROCESS] Adding to end of message.")
                print(f"\t'{message_data}' += '{read_message}'")
                message         += read_message
                remaining_bytes -= read_bytes
            else: 
                print("[MSG_PROCESS] Client disconnected.")
                print(f'\t> `{message}')
                message         = b""
                remaining_bytes = 0

        return client_connected, remaining_bytes, message


    # Retrieve incoming message data.
    def s_receive_message(self, socket, size):
        print("[MSG_RECEIVE] Receiving message data.")
        message = ""
        read_bytes = 0
        client_connected = True

        try: 
            message = socket.recv(size)        # reads all message, but will change
            read_bytes = sys.getsizeof(message)
            # message = message.decode("utf-8")
        except:
            print("[MSG_RECEIVE] ERROR: Message receiving encountered an issue; disconnecting.")
            client_connected = False
    
        return client_connected, message, read_bytes


    def s_send_message(self, sock, message):
        send_message = message.encode(FORMAT)
        message_length = len(send_message)

        send_len = str(message_length).encode("utf-8")
        send_len += b' ' * (HEADER_SIZE - len(send_len))

        sock.send(send_len)
        sock.send(send_message)



    def s_return_message(self, socket):
        client_connected = True
        message = "DATA RECEIVED"

        try:
            self.s_send_message(socket, message)
        except:
            client_connected = False
            message = ""

        return client_connected, message







###########################



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

if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'server.py'; file 'server_library.py' is a module only.")
  exit()
  