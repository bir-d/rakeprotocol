# Execute me for a simplified example of server-client communication.
from parser import Rake
from executor import Executor
from client import Client

if __name__ == '__main__':
  rakeData    = Rake("Project/Rakefile")
  rakep       = Client(rakeData)
  rakeserver  = Executor("rakeserver")
  
  rakep.requestExecution(rakeserver)