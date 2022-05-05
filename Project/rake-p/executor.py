import os 
import datetime
import subprocess

# TODO: Revise code to be based.
#         - client based logs rather than server
#         - client based temporary directories rather than server
#         - handle errors with more precisions (detailed below)

# Server objects manage the execution and handling of client requests. 
class Server:
  def __init__(self, hostname, verbose=False):
    print("[rakeserver] Server execution instance initialised.\n")
    self.online     = True
    self.hostname   = hostname
    self.queue      = list()
    self.commandID  = 1   # Potentially add where a commandID is from.
     
    # There will probably be a few sockets based on client 
    self.socket     = ""    
    self.logname    = self.hostname+"_log"
    self.direxists  = False

    print("[rakeserver] Creating temporary folder for host...")

    # Tries to make directory, uses existing dir if exists.
    # Cormac: if fails to make dir due to perms, could potentially still execute
    #         explicit check for directory required as OSError too broad.
    try: 
      os.mkdir(hostname+"_tmp",)
      print("[rakeserver] Folder created.")
    except OSError as error:  # Consider revision.
      self.direxists = True
      print("[rakeserver] Folder already exists, using existing folder.")

    os.chdir(hostname+"_tmp")
    print("[rakeserver] Set current directory to host's temporary folder.\n")
    print("[rakeserver] Creating log file for "+self.hostname+"...")

    # Same error as above, what if issues are permission related, not
    #   existing file related? How should this be handled?
    try:
      f = open(self.logname, "x")
      f.write("### "+self.hostname+" Log ###\n")
      f.write()
      print("[rakeserver] Created file successfully.\n")
    except:
      f = open(self.logname, "a")
      f.write("\n" + self.timestamp()+" Appending to existing server log.\n")
      print("[rakeserver] Found existing log for host!\n")

    self.log = f

  def timestamp(self):
    now = datetime.datetime.now()
    date_time = now.strftime("(%m/%d/%Y %H:%M:%S)")
    return date_time	

  def runCommand(self):
    command = self.queue.pop(0)

    self.log.write(self.timestamp()+ " ["+str(self.commandID)+"] > "+command+"\n")
    try:
      exec = subprocess.check_output([command], shell=True, stderr=subprocess.STDOUT, text=True)
      self.log.write(self.timestamp()+" ["+str(self.commandID)+"] Executed successfully.\n")
      self.log.write("stdout: " + exec + "\n")
    except subprocess.CalledProcessError as error:
      self.log.write(self.timestamp()+" ["+str(self.commandID)+"] Execution failed.\n")
      # self.log.write("stderr:"+repr(error)) # this is the PYTHON error not stdout
    print("[rakeserver] Executed command.")
    self.commandID+=1
      
  def addCommand(self, command, clientName):
    self.log.write(self.timestamp()+" Recieved command request from '"+clientName+"'.\n")
    self.queue.append(command)
    print("[rakeserver] Command added to execution queue.")

  def setOffline(self):
    self.online = False
    self.log.write(self.timestamp()+" Host taken offline.\n")

  def setOnline(self):
    self.online = True
    self.log.write(self.timestamp()+" Host back online.\n")