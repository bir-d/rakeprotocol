from server import Server
from parser import Parser
import socket
import os

Rakefile = "Project/Rakefile"

if __name__ == '__main__':
  rakeserver_dir = os.getcwd().replace("/rakeserver", "/Rakefile")
  rakeData  = Parser(rakeserver_dir, verbose=True)
  servers   = list()
  
  for host in rakeData.hosts:
    servers.append(Server(host))
  
