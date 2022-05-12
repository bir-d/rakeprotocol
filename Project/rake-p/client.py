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
    print("\n"+defaultRakefilePath+"\n")
    RakefilePath    = defaultRakefilePath
  except:
    print("[r.p]\tRakefile not found at path: \n\t'"+sys.argv[1]+"'")
    exit()
  
  # Extract information from Rakefile.
  rakefileData  = Parser(RakefilePath)

  # Uses Parser object to populate client data.
  print("\n[r.p]\tInstantiating client.")
  rakeClient   = Client(rakefileData)

  print("\n[r.p]\tCreating tmp directories for each server.")
  dirNav = DirectoryNavigator(os.getcwd())
  for host in rakeClient.hosts:
    dirNav.createDir(host + "_tmp")


  print("\n[r.p]\tEstablishing sockets for communication with hosts.")
  for hostname in rakeClient.hosts:
    host, port = hostname.split(":")
    socket = SocketHandling(host, int(port))
    rakeClient.addSocket(hostname, socket)

  # From here, code is unstable and incomplete.
  print("\n\n----[DEBUG]----\n")
  print("\n[r.p]\tSending command.")

  commandTest = rakeClient.actionsets[0][0]
  socketTest  = rakeClient.sockets["127.0.0.1:6238"]
  socketTest.connect(commandTest)
  socketTest.awaitServer()
    # socket.initiateListening()
    # rakeClient.addSocket(socket)
