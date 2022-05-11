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
    defaultRakefilePath = "/".join(os.getcwd().split("/")[:-1]) + "/Rakefile"
    print("[r.s]\tLocating Rakefile.")
    try:
        RakefilePath    = sys.argv[1]
        print(" |-> [rakefile]  Using path given to find Rakefile.")
    except IndexError:
        print(" |-> [rakefile]  No Rakefile specified, using default path:")
        print(" |\t'"+defaultRakefilePath+"'")
        RakefilePath    = defaultRakefilePath
    except:
        print(" |-> [rakefile]  Rakefile not found at path: \n\t'" + sys.argv[1] + "'")
        exit()

    # Extract information from Rakefile.
    print("\n[r.s]\tAnalysing Rakefile information.")
    rakefileData  = Parser(RakefilePath)

    # Uses Parser object to populate client data.
    print("\n[r.s]\tInstantiating server.")
    rakeServer   = Server(rakefileData)

    print("\n[r.s]\tCreating tmp directories for each host.")
    dirNav = DirectoryNavigator(os.getcwd())
    for host in rakefileData.hosts:
        dirNav.createDir(host + "_tmp")
  
    print("\n[r.s]\tEstablishing socket for communication with clients.")
    host, port = rakefileData.hosts[0].split(":")
    socket = SocketHandling(host, int(port))
    socket.initiateListening()
    # for host in rakeServer.hosts:
    #     host, port = host.split(":")
    #     socket = SocketHandling(host, int(port))
    #     socket.initiateListening()
    #     rakeServer.addSocket(socket)

    print("\n[r.s]\tPreparing server to recieve commands.")
    socket.awaitClient()



    
