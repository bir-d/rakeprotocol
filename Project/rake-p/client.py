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
  defaultRakefilePath = "/".join(os.getcwd().split("/")[:-1]) + "/Rakefile"
  print("[r.p]\tLocating Rakefile.")
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
  print("\n[r.p]\tAnalysing Rakefile information.")
  rakefileData  = Parser(RakefilePath)

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
    socket.startConnection()
    socket.awaitClient()
    # socket.initiateListening()
    rakeClient.addSocket(socket)
  
  print("\n[r.s]\tSending commands to server.")
  


  # Starts the server using it's hostname.
  # rakeserver  = Server("rakeserver")
  
  # Checks for available servers, requesting actionset,
  #   exectution or queuing commands to server which
  #   has the smallest queue size (not currently implemented).
  # rakep.connectToHost(rakeserver)
  # rakep.requestExecution()
