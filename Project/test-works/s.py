# RASPBERRY PI STORAGE

import os
import socket
import threading
import subprocess
import errno

PORT    = 5051
SERVER  = '192.168.0.3'
ADDR    = (SERVER,PORT)

class Comms:
    HEADER = 64
    FORMAT = 'utf-8'

class Codes:
    DISCONN_MSG     = "!D"
    COMMAND_MSG     = "!C"
    REQUEST_MSG     = "!R"
    SUCCEED_RSP     = "!S"
    FAILURE_RSP     = "!F"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"NEW: {addr[0]}:{str(addr[1])}")
    connected = True

    while connected:
        # blocks til recieve msg from client
        msg_type = conn.recv(2).decode(Comms.FORMAT) 

        # Received no message, just connection.
        if msg_type == "":
            pass
        # Received request to disconnect.
        elif msg_type == Codes.DISCONN_MSG:
            connected = False
        # Received servable request.
        else:
            msg_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
            msg_length = int(msg_length)

            if msg_type == Codes.COMMAND_MSG:
                msg = conn.recv(msg_length).decode(Comms.FORMAT) 
                try:
                    execute_command(msg, addr)
                    conn.send(Codes.SUCCEED_RSP.encode(Comms.FORMAT))
                except:
                    conn.send(Codes.FAILURE_RSP.encode(Comms.FORMAT))
            
            elif msg_type == Codes.REQUEST_MSG:
                name_length = conn.recv(Comms.HEADER).decode(Comms.FORMAT) 
                name_length = int(name_length)
                name = conn.recv(name_length).decode(Comms.FORMAT) 
                msg = conn.recv(msg_length).decode(Comms.FORMAT) 
                try:
                    get_requirement(name, msg, conn, addr)
                    conn.send(Codes.SUCCEED_RSP.encode(Comms.FORMAT))
                except:
                    conn.send(Codes.FAILURE_RSP.encode(Comms.FORMAT))

    conn.close()

def get_requirement(name, msg, conn, addr):
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

def execute_command(msg, addr):
    message = msg.split()
    print(f"[{addr[0]}:{str(addr[1])}] Command execution output:")
    with subprocess.Popen(message, stdout=subprocess.PIPE) as proc:
        print("> "+proc.stdout.read().decode(Comms.FORMAT))

def start():
    server.listen()
    print(f"Server listening on: {SERVER}")
    while True:
        # conn is socket, addr is host(ip:port)
        conn, addr = server.accept() # blocks til connected

        # send socket and host to handle_client()
        thread = threading.Thread(  target=handle_client, args=(conn, addr))
        thread.start()
        print(f"(active: {threading.activeCount() - 1})\n")


print("Starting server.")
start()

