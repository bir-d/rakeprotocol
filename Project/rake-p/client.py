''' 
TODO: Implement multiple client management.
- Requires refactoring of how Client objects function/what they store.
- Initially single client for simplicity 
'''

import socket
import os
import sys

from client_library import Parser, Client, DirectoryNavigator, SocketHandling

if __name__ == '__main__':
  defaultRakefilePath = "/".join(os.getcwd().split("/")[:-1]) \
                          + "/Rakefile"

  print("[r.p]\tSearching for Rakefile...")
  try:
    RakefilePath    = sys.argv[1]
    print("[r.p]\tUsing path given to find Rakefile.")
  except IndexError:
    print("[r.p]\tNo Rakefile specified, using default path.")
    RakefilePath    = defaultRakefilePath
  except:
    print("[r.p]\tRakefile not found at path: \n\t'"+sys.argv[1]+"'")
    exit()
  
  # Extract information from Rakefile.
  rakefileData  = Parser(RakefilePath)

  # print("\n[r.p]\tInitiating client management.")
  # ClientManager = ClientManagement(rakefileData)

  # Uses Parser object to populate client data.
  print("\n[r.p]\tInstantiating client.")
  rakeClient   = Client(rakefileData)

  print("\n[r.p]\tCreating tmp directories for each host.")
  dirNav = DirectoryNavigator(os.getcwd())
  for host in rakeClient.hosts:
    dirNav.createDir(host + "_tmp")

  print("\n[r.p]\tEstablishing sockets for communication with hosts.")
  for host in rakeClient.hosts:
    host, port = host.split(":")
    socket = SocketHandling(host, int(port))
    socket.initiateListening()
    rakeClient.addSocket(socket)



  # Starts the server using it's hostname.
  # rakeserver  = Server("rakeserver")
  
  # Checks for available servers, requesting actionset,
  #   exectution or queuing commands to server which
  #   has the smallest queue size (not currently implemented).
  # rakep.connectToHost(rakeserver)
  # rakep.requestExecution()
