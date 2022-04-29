# Manages the connections described by the Rakefile.
PATH_Rakefile = 'Project/Rakefile'

# def readRakefile(filepath, verbose=False):
#   print("[rake.p] Reading Rakefile at '" + filepath + "'.")
#   f = open(filepath)
#   Rakefile = f.readlines()
#   f.close()

#   print("[rake.p] Read completed.")
#   if verbose:
#     print("[rake.p] Printing Rakefile.")
#     for line in Rakefile:
#       print("> " + line)
#     print("---")
  
#   return Rakefile

def readRakefile(filepath, verbose=False):
  print("[rake.p] Reading Rakefile at '" + filepath + "'.")

  with open(filepath, "r") as f:
    line = f.readline()
    index = 0

    while line:
      if line.startswith("#") or len(line.split()) == 0:
        None
      elif line.startswith("PORT  ="):
        PORT = line.replace("PORT  =","").strip()
      elif line.startswith("HOSTS ="):
        HOSTS = line.replace("HOSTS =","").split() 
      else: # distinguish remote and local actions
        # "tabs" in chris notes are spaces in the example... 
        action = line.replace("    ", "\t")
        if "\t\t" in action:
          requirement = action.replace("\t\trequires ", "").split()
          print("REQ:",requirement)
        elif "\t" in action:
          if action.startswith("\tremote-"):
            remoteCommand = action.replace("\tremote-", "").strip()
            print("R:", remoteCommand)
          else:
            localCommand = action.replace("\t", "").strip()
            print("L:", localCommand)
        else:
          actionSet = action.replace(":","").strip()
          print(actionSet)

        # line = f.readline()

      line = f.readline()
      index += 1

  print("[rake.p] Read completed.")
  # if verbose:
  #   print("[rake.p] Printing Rakefile.")
  #   for line in Rakefile:
  #     print("> " + line)
  #   print("---")
  
  return 0


# Parses details for the connection (Port, Hosts, and Action Sets)
# TODO: Needs heavy simplifying, probably can do this in the reading file part.
def getConnectionDetails(Rakefile):
  i, actionSet = 0, Rakefile

  while i < len(actionSet):
    # Finds the port number (only one)
    if actionSet[i].startswith("PORT"):
      portNum = actionSet[i].replace("PORT  = ", "", 1)
      actionSet.pop(i)

    # Finds the hosts (at least one)
    elif actionSet[i].startswith("HOSTS = "):
      hostList = actionSet[i].replace("HOSTS = ", "", 1).split(" ")
      actionSet.pop(i)

    # Finds all other empty lines
    elif actionSet[i] != "\n":
      # If the line does not start with 8 spaces (two tabs) then it is a command
      if not actionSet[i].startswith("        "):
        # %COM% identifies a command.
        actionSet[i] = actionSet[i].replace("    ", "%COM%").replace("\n", "")
      # If the line starts with 8 spaces, it is a requirement.
      elif actionSet[i].startswith("        "):
        # %REQ% identifies a requirement.
        actionSet[i] = actionSet[i].replace("        ", "%REQ%").replace("\n", "")
      i+=1

    # Remove all other lines.
    else:
      actionSet.pop(i)
        
  # TODO: Pair all commands with their requirements.

  return portNum, hostList, actionSet

# --------------------------------------------


if __name__ == '__main__':
  print("[rake.p] Initialised.")
  Rakefile = readRakefile(PATH_Rakefile)
  # (PORT, HOSTS, ACTIONS) = getConnectionDetails(Rakefile)
  # print("[rake.p] Printing PORT.")
  # print("| " + PORT)

  # print("[rake.p] Printing HOSTS.")
  # for i in HOSTS:
  #   print("| " + i)
    
  # print("[rake.p] Printing ACTIONS.")
  # for i in ACTIONS:
  #   print("| " + i)


  
# class Connection:
#   def __init__(self, portNum, hostList, actions, verbose=False):
#     self.PORT     = portNum
#     self.HOSTS    = [i for i in hostList]
#     self.ACTIONS  = actions

#     if verbose:
#       print("[rake.p] PORT:", self.PORT)
#       print("[rake.p] HOSTS:")
#       for i in self.HOSTS:
#         print(i, sep=" ")
  
#   def reportConnection(self):
#     print("[rake.p]\n","PORT:\n", self.PORT, "\nHOSTS:")
#     for i in self.HOSTS:
#       print("> ", i)
  














