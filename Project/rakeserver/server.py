import socket
import sys
import os

from server_library import Server, DirectoryNavigator, SocketHandling

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("[r.s]\tArgument error; usage <host> <port>")
        sys.exit(1)

    # Uses Parser object to populate client data.
    print("\n[r.s]\tInstantiating Server.")
    server   = Server(sys.argv[1], sys.argv[2])

    print("\n[r.s]\tCreating tmp directory for host.")
    dirNav = DirectoryNavigator(os.getcwd())
    dirNav.createDir(server.host+":"+str(server.port) + "_tmp")
  
    print("\n[r.s]\tEstablishing socket for communication with clients.")
    socket = SocketHandling(server.host, server.port)
    socket.initiateListening()
    socket.awaitClient()


