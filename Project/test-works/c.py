import socket

PORT    = 5050
SERVER  = '192.168.0.3'
ADDR    = (SERVER,PORT)
HEADER  = 64

DISCONNECT_MESSAGE  = "!D"
COMMAND_MESSAGE     = "!C"
REQUIREMENT_MESSAGE = "!R"

FORMAT  = 'utf-8'

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send_requirement(path):
    name = path.split("/")[-1].encode(FORMAT)

    with open(path) as f:
        msg = f.read()
    message = msg.encode(FORMAT)

    msg_length = len(message)
    name_length = len(name)

    send_msg_length = str(msg_length).encode(FORMAT)
    send_msg_length += b' ' * (HEADER - len(send_msg_length))

    send_name_length = str(name_length).encode(FORMAT)
    send_name_length += b' ' * (HEADER - len(send_name_length))

    client.send(send_msg_length)
    client.send(send_name_length)
    client.send(name)
    client.send(message)
    
    print(client.recv(2048).decode(FORMAT))

def send_command(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    print(client.recv(2048).decode(FORMAT))

def send(type, val="", path="", name=""):
    if type == COMMAND_MESSAGE:
        client.send(type.encode(FORMAT))
        send_command(val)
    elif type == REQUIREMENT_MESSAGE:
        client.send(type.encode(FORMAT))
        send_requirement(path)
    elif type == DISCONNECT_MESSAGE:
        client.send(type.encode(FORMAT))

file = "/Users/jamiemccullough/Library/Mobile Documents/com~apple~CloudDocs/Documents/University/Semesters/2022-s1/Networks Project/Project/jamienotes/testingsockets/test2"

send(REQUIREMENT_MESSAGE, path=file)

send(COMMAND_MESSAGE, val="echo Server test.")
send(COMMAND_MESSAGE, "cat test2")
send(COMMAND_MESSAGE, "rm test2")
send(DISCONNECT_MESSAGE, "")



