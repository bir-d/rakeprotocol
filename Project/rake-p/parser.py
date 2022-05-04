import os 

class Rake:
  def __init__(self, path=""):
    print("[rake.p] Initialising Rakefile object.")
    self.path   = path
    self.curdir = os.getcwd()

    self.port   = 0
    self.hosts  = list()
    self.actionsets = list()

    self.readRakefile()

  def printRakeDetails(self):
    if self.actionsets and self.hosts :
      print("[rake.p] Printing results...")
      print("> PORT:", self.port)
      print("> HOSTS:", self.hosts)

      for actionNum, commands in enumerate(self.actionsets):
        print("> actionset"+ str(actionNum+1))
        for command in commands:
          print(">>", command)
        print('')
      print("[rake.p] Completed result printing.\n")
    else:
      print("[rake.p] No Rakefile parsed.")

  def readRakefile(self):
    if self.path =="": 
      self.path = self.curdir + "/Rakefile"
    
    print("[rake.p] Reading Rakefile at '" + self.path + "'...")
    try:
      with open(self.path, "r") as f:
        line = f.readline().replace("    ", "\t")   # Sets 4 spaces to tab character.

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
            self.actionsets.append(commands) # Adds the commands of the ACTIONSET to the list of ACTIONSETS.
          else:
            # Line holds PORT number, which is stored as an integer.
            if line.startswith("#") or len(line.strip()) == 0:
              None
            elif line.startswith("PORT  ="):
              self.port = line.replace("PORT  =","").strip()
            # Line holds HOSTS, which are split and stored as a list.
            elif line.startswith("HOSTS ="):
              self.hosts = line.replace("HOSTS =","").split() 

            line = f.readline().replace("    ", "\t")

      print("[rake.p] Read completed.\n")
    
    except:
      return FileNotFoundError("[read.p] Error: No Rakefile found.")


        














