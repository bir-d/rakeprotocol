import socket
import os
import sys
import client_library 

if __name__ == '__main__':
  # sys.stdout = open('client_log.dat', 'w')
  defaultRakefilePath = "/".join(os.getcwd().split("/")[:-1]) + "/Rakefile"

  print("[r.p]\tSearching for Rakefile...")
  try:
    RakefilePath    = sys.argv[1]
    print("[r.p]\tUsing path given to find Rakefile.")
  except IndexError:
    print("[r.p]\tNo Rakefile specified, using default path.")
    print(" |\n |\t"+defaultRakefilePath+"\n |")
    RakefilePath    = defaultRakefilePath
  except:
    print("[r.p]\tRakefile not found at path: \n\t'"+sys.argv[1]+"'")
    exit()
  
  # Extract information from Rakefile.
  rakefileData  = client_library.Parser(RakefilePath)

  # Uses Parser object to populate client data.
  print("\n[r.p]\tInstantiating client.")
  client   = client_library.Client(rakefileData)

  # FOLLOWING ONLY WORKS FOR ONE SERVER
  #   - NO MULTICLIENT ABILITY
  #   - NO MULTISERVER ABILITY
  #   - NO COST CALCULATION
  client.DEBUG_send("Test.")


  
