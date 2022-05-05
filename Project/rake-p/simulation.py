# simulation.py #
# Execute for simple server-client communication.
from parser   import Parser     # Handles Rakefile
from executor import Server     # Fake "Server" 
from client   import Client     # Manages client requests

if __name__ == '__main__':
  # Extract Rakefile data into data structures.
  rakeData    = Parser("Project/Rakefile")

  # Takes the Parser object stores client information.
  rakep       = Client(rakeData)

  # Starts the server using it's hostname.
  rakeserver  = Server("rakeserver")
  
  # Checks for available servers, requesting actionset
  #   exectution or queuing commands to server which
  #   has the smallest queue size (not currently implemented).
  rakep.requestExecution(rakeserver)