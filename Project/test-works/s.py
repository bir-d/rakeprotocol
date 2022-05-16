import os
import socket
import threading
import subprocess
import errno

PORT    = 5050
SERVER  = '192.168.0.3'
ADDR    = (SERVER,PORT)
HEADER  = 64

DISCONNECT_MESSAGE  = "!D"
COMMAND_MESSAGE     = "!C"
REQUIREMENT_MESSAGE = "!R"

FORMAT  = 'utf-8'


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"New Connection: {addr}")
    connected = True

    while connected:
        # blocks til recieve msg from client
        msg_type = conn.recv(2).decode(FORMAT) 
        if msg_type == DISCONNECT_MESSAGE:
            connected = False
        else:
            msg_length = conn.recv(HEADER).decode(FORMAT) 
            msg_length = int(msg_length)

            if msg_type == COMMAND_MESSAGE:
                msg = conn.recv(msg_length).decode(FORMAT) 
                try:
                    execute_command(msg)
                    conn.send(f"{addr}: Command recieved.".encode(FORMAT))
                except:
                    conn.send(f"{addr}: Command successful.".encode(FORMAT))
            
            elif msg_type == REQUIREMENT_MESSAGE:
                name_length = conn.recv(HEADER).decode(FORMAT) 
                name_length = int(name_length)
                name = conn.recv(name_length).decode(FORMAT) 
                msg = conn.recv(msg_length).decode(FORMAT) 
                try:
                    get_requirement(name, msg, conn, addr)
                except:
                    conn.send(f"{addr}: Requirement failed.".encode(FORMAT))
    conn.close()

def get_requirement(name, msg, conn, addr):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY

    try:
        file = os.open(name, flags)
    except OSError as error:
        if error.errno == errno.EEXIST:
            conn.send(f"{addr}: File exists.".encode(FORMAT))
        else: 
            raise
    else:
        with open(file, 'w') as file:
            file.write(msg)
        conn.send(f"{addr}: File recieved.".encode(FORMAT))

def start():
    server.listen()
    print(f"Server listening on: {SERVER}")
    while True:
        # conn is socket, addr is host(ip:port)
        conn, addr = server.accept() # blocks til connected

        # send socket and host to handle_client()
        thread = threading.Thread(  target=handle_client, args=(conn, addr))
        thread.start()
        print(f"ACTIVE: {threading.activeCount() - 1}\n")

def execute_command(msg):
    message = msg.split()

    with subprocess.Popen(message, stdout=subprocess.PIPE) as proc:
        print(proc.stdout.read().decode(FORMAT))

def start():
    server.listen()
    print(f"Server listening on: {SERVER}")
    while True:
        # conn is socket, addr is host(ip:port)
        conn, addr = server.accept() # blocks til connected

        # send socket and host to handle_client()
        thread = threading.Thread(  target=handle_client, args=(conn, addr))
        thread.start()
        print(f"ACTIVE: {threading.activeCount() - 1}\n")


print("Starting server.")
start()

