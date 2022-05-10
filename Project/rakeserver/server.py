import os 
import datetime
import subprocess

# TODO: Revise code to be based.
#         - client based logs rather than server
#         - client based temporary directories rather than server

# Server objects manage the execution and handling of client requests. 
class Server:
  def __init__(self, hostname):
    print(hostname)
    print("\n[rakeserver] Server execution instance initialised for host:"+hostname+".")
    self.online     = True
    self.hostname   = hostname
    self.queue      = list()
    self.clients    = dict()

    print("[rakeserver] Creating temporary folder for communications...")

    # Makes directory or uses existing dir.
    dirPath = self.createDir(self.hostname+"_data") 

    if dirPath == OSError:
      print("[rakeserver] Terminating server instance. #ERR_MKDIR_HOST")
      exit()
    elif not self.dirExists(dirPath):
      print("[rakeserver] Terminating server instance. #ERR_CHDIR_HOST")
      exit()

    # Directory exists, saved and changed into.
    self.hostDir = dirPath

  # Creates a directory in the 
  def createDir(self, dirName):
    try: 
      os.mkdir(dirName)
      print("[rakeserver] Folder '"+dirName+"' created.")
    except FileExistsError:  # Thrown where dir exists
      print("[rakeserver] Folder '"+dirName+"' already exists, using existing folder.")
    except: # Any other errors must halt execution 
      print("[rakeserver] ERROR: Cannot access or create directory.")
      return OSError
    return os.getcwd() + "/" + dirName 

  # Determines if the directory path exists - relative or absolute.  
  def dirExists(self, dirPath):
    if os.path.exists(dirPath) or os.path.exists(os.getcwd()+"/"+dirPath):
      return True
    else:
      print("[rakeserver] ERROR: Failed to find directory '"+dirPath+"'!")
      return False

  # Handles the initial onboarding of clients with the server.
  def connectToClient(self, clientName):
    print("[rakeserver] Received connection request from '"+clientName+"' recieved.")
    clientDir = self.createDir(clientName)

    if clientDir == OSError:
      print("[rakeserver] Terminating server instance. #ERR_MKDIR_HOST")
      return -1
    elif not self.dirExists(clientDir):
      print("[rakeserver] Terminating connection to client. #ERR_CHDIR_CLIENT")
      return -1

    os.chdir(clientDir)
    print("[rakeserver] Creating log file for '"+clientName+"'...")
    try: 
      log = open(clientName+"_tmp", "x")
      log.write("### "+clientName+" Log ###\n")
      log.write("\n" + self.timestamp()+" Log created.\n")
      
      print("[rakeserver] Created file successfully.\n")
    except FileExistsError: # Log file for client exists already.
      log = open(clientName+"_tmp", "a")
      log.write("\n---\n" + self.timestamp()+" Found existing client log.\n")
      print("[rakeserver] Found existing log for host!\n")
    except:
      print("[rakeserver] ERROR: Cannot create log file or access existing log file.\n")
      return False

    self.clients[clientName] = log
    # close log

    print("[rakeserver] Connected to client '"+clientName+"'.")


  def timestamp(self):
    now = datetime.datetime.now()
    date_time = now.strftime("(%m/%d/%Y %H:%M:%S)")
    return date_time	

  def runCommands(self):
    if len(self.queue) >= 0:
      command = self.queue.pop(0)
      self.log.write(self.timestamp()+ " > "+command+"\n")
      try:
        exec = subprocess.check_output([command], shell=True, stderr=subprocess.STDOUT, text=True)
        self.log.write(self.timestamp()+" Executed successfully.\n")
        self.log.write("stdout: \n\t'" + exec + "'\n")
      except subprocess.CalledProcessError as error:
        self.log.write(self.timestamp()+" Execution failed: returned non-zero execution status.\n")
        print(repr(error))
        self.log.write("stderr:"+repr(error)) # this is the PYTHON error not stdout
      print("[rakeserver] Executed command.")

      self.commandID+=1

      # Calls self until queue full, then halts execution: this code is
      #   trying to demonstrate that the queue is checked again at the
      #   end of executing each command. In reality, this still doesn't
      #   do this, but hey... it's a start :)
      self.runCommands() 
    else:
      print("[rakeserver] Queue contains no commands to execute.")
      
  def getExecutionCost(self):
    return len(self.queue)

  def getClientDirPath(self, clientName):
    currentDir = os.getcwd()
    path = currentDir.split("/")

    if path[-1]   == self.hostname: # CD = host directory
      return currentDir+ "/" + clientName
    elif path[-1] == clientName:    # CD = client directory
      return currentDir 
    elif self.hostname in path:     # CD has the hostname in it's path 
      # TODO: Check that just not a dir with same name as host.
      index = path.indexOf(self.hostname)
      return '/'+ "/".join(path[:index+1])+ "/" + clientName 
    else:
      return OSError

  def addCommand(self, command, clientName):
    clientPath = self.getClientDirPath(clientName)
    if clientPath != OSError:
      os.chdir(clientPath)
      self.clientLogs[clientName].write(self.timestamp()+" Recieved command request.\n")
      self.queue.append(command)
      print("[rakeserver] Command added to execution queue.")
    else:
      print("[rakeserver] ERROR: Failed to add command to queue of host'"+self.hostname+"'.")
      return -1
    return len(self.queue) - 1


if __name__ == '__main__':
  print("ERROR: Incorrect file run. \nPlease run 'rakeserver.py'; file 'server.py' is a module only.")
  exit()
  