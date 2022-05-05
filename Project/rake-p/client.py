class Client: 
  def __init__(self, rakeData):
    print("[rake.p] Initialised Python rake client.\n")
    self.port         = rakeData.port
    self.hosts        = rakeData.hosts
    self.actionsets   = rakeData.actionsets

  # def pollHosts(self):
  #   availableHosts = list()
  #   for host in self.hosts:
  #     # if host is not busy:
  #     availableHosts.append(host)
  #   return availableHosts

  # Connect client to host; currently naive.
  # TODO: Implement hostname/port connection.
  def connectToHost(self, Server):
    Server.connectToClient('rakep')
    print("[rake.p] Connected to host '"+Server.hostname+"'.")
    self.Server = Server

  # Finds an available host to execute on.
  def executeActionsets(self):
    for actionset in self.actionsets:
      availableHosts = self.pollHosts()
      while len(availableHosts) > 0:
        command = actionset.pop(0)
        host    = availableHosts.pop(0)
        # send command to host (hostname probably passed to server?)
        # how do we wait for results?

  # CURRENTLY AN EXTREMELY NAIVE, DEMONSTRATIVE FUNCTION 
  # TODO: Implement host routing for commands based on lowest execution cost. 
  # TODO: Move running of command to the Server code, rather than client.
  def requestExecution(self):
    try:
      for command in self.actionsets[0]:
        self.Server.addCommand(command, "rakep")
    except:
      print("[rake.p] ERROR: Could not connect to server.")

