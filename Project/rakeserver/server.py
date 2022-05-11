''' 
TODO: Implement multiple server management.
- Requires refactoring of how Server objects function/what they store.
- Initially single server for simplicity 
'''


import socket
import sys
import os

from server_library import Parser, Server, DirectoryNavigator, SocketHandling

if __name__ == '__main__':
    defaultRakefilePath = "/".join(os.getcwd().split("/")[:-1]) \
                            + "/Rakefile"
    print("[r.s]\tSearching for Rakefile...")

    try:
        RakefilePath    = sys.argv[1]
        print("[r.s]\tUsing path given to find Rakefile.")
    except IndexError:
        print("[r.s]\tNo Rakefile specified, using default path.")
        RakefilePath    = defaultRakefilePath
    except:
        print("[r.s]\tRakefile not found at path: \n\t'" + sys.argv[1] + "'")
        exit()

    # Extract information from Rakefile.
    rakefileData  = Parser(RakefilePath)

    # print("\n[r.s]\tInitiating server management.")
    # ServerManager = ServerManagement(rakefileData)

    # Uses Parser object to populate client data.
    # print("\n[r.s]\tCreating servers for each host.")
    # for host in rakefileData.hosts:
    #     rakeServer   = Server(host)
    #     ServerManager.addServer(rakeServer)

    # Uses Parser object to populate client data.
    print("\n[r.s]\tInstantiating server.")
    rakeServer   = Server(rakefileData)

    print("\n[r.s]\tCreating tmp directories for each host.")
    dirNav = DirectoryNavigator(os.getcwd())
    for host in rakeServer.hosts:
        dirNav.createDir(host + "_tmp")
  
    print("\n[r.s]\tEstablishing sockets for communication with hosts.")
    for host in rakeServer.hosts:
        host, port = host.split(":")
        socket = SocketHandling(host, int(port))
        socket.initiateListening()
        rakeServer.addSocket(socket)
