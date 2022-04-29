# Manages the connections described by the Rakefile.
PATH_Rakefile = 'Project/Rakefile'

# Reads in the Rakefile, stores the values in data structures.
# Note: The "tabs" in the example are spaces in the text,
#       so readline also replaces 4 spaces to be '\t' 
def readRakefile(filepath, verbose=False):
  print("[rake.p] Reading Rakefile at '" + filepath + "'...")

  with open(filepath, "r") as f:
    line = f.readline().replace("    ", "\t")   # Sets 4 spaces to tab character.
    ACTIONSETS = list()     # List of commands (which are lists too)

    while line:
      if line.startswith("actionset"):
        commands = list()   # List of commands found in an ACTIONSETS.
        line = f.readline().replace("    ", "\t")

        # Commands/requirements of ACTIONSET must start with at least one tab.
        while line.startswith("\t"):
          if line.startswith("\tremote-"):  # Indicates command is executed remotely.
            command = [ "remote",  line.strip().replace("remote-", "")]
          else:                             # Indicates command is executed locally.
            command = [ "local",   line.strip()]
            
          # Increments line to check for potential requirements.
          line = f.readline().replace("    ", "\t") 

          if line.startswith("\t\t"):   # Requirement lines use two tab characters.
            # Add requirements as list to the end of the command list.
            command.append( line.replace("\t\trequires ", "").split() ) 
            line = f.readline().replace("    ", "\t")
          else:                         # No requirements for above command.
            # Append empty list of requirements to the end of command list.
            command.append( [] )
          commands.append(command)  # Adds command above to current ACTIONSET commands.
        ACTIONSETS.append(commands) # Adds the commands of the ACTIONSET to the list of ACTIONSETS.
      else:
        # Line is a comment or is whitespace only/
        if line.startswith("#") or len(line.strip()) == 0:
          None
        # Line holds PORT number, which is stored as an integer.
        elif line.startswith("PORT  ="):
          PORT = line.replace("PORT  =","").strip()
        # Line holds HOSTS, which are split and stored as a list.
        elif line.startswith("HOSTS ="):
          HOSTS = line.replace("HOSTS =","").split() 

        line = f.readline().replace("    ", "\t")

    print("[rake.p] Read completed.\n")
            
    # Prints out the PORT HOSTS and ACTIONSET details.
    if verbose:
      print("[rake.p] Printing results...")
      print("> PORT:", PORT)
      print("> HOSTS:", HOSTS)
      for actionNum, commands in enumerate(ACTIONSETS):
        print("> actionset"+ str(actionNum))
        for command in commands:
          print(">", command)
      print("[rake.p] Completed result printing.\n")
      
    return (PORT, HOSTS, ACTIONSETS)

# --------------------------------------------

if __name__ == '__main__':
  print("[rake.p] Initialised Python rake client.\n")
  PORT, HOSTS, ACTIONSETS = readRakefile(PATH_Rakefile, True)
  













