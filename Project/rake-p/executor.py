import os 
import datetime
import subprocess

class Executor:
  def __init__(self, hostname):
    print("[rakeserver] Server execution instance initialised.\n")
    self.online     = True
    self.hostname   = hostname
    self.queue      = list()
    self.commandID  = 0
    self.socket     = ""
    self.logname    = self.hostname+"_log"
    self.direxists  = False
    print("[rakeserver] Creating temporary folder for host...")

    try: 
      os.mkdir(hostname+"_tmp",)
      print("[rakeserver] Folder created.")
    except OSError as error: 
      self.direxists = True
      print("[rakeserver] Folder already exists, using existing folder.")

    os.chdir(hostname+"_tmp")
    print("[rakeserver] Set current directory to host's temporary folder.\n")
    print("[rakeserver] Creating log file for "+self.hostname+"...")

    try:
      f = open(self.logname, "x")
      f.write("### "+self.hostname+" Log ###\n")
      f.write()
      print("[rakeserver] Created file successfully.\n")

    except:
      f = open(self.logname, "a")
      f.write("\n" + self.timestamp()+" ["+str(self.commandID)+"] Appending to existing server log.\n")
      print("[rakeserver] Found existing log for host!\n")

    self.log = f

  def timestamp(self):
    now = datetime.datetime.now()
    date_time = now.strftime("(%m/%d/%Y %H:%M:%S)")
    return date_time	

  def runCommand(self):
    command = self.queue.pop()
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
    self.commandID+=1

  def setOnline(self):
    self.online = True
    self.log.write(self.timestamp()+" Host back online.\n")
    self.commandID+=1