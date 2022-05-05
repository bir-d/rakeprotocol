class Client: 
  def __init__(self, rakeData):
    print("[rake.p] Initialised Python rake client.\n")
    self.port         = rakeData.port
    self.hosts        = rakeData.hosts
    self.actionsets   = rakeData.actionsets

  # Is not able to see if the server is busy
  # simply a naive execution script
  # TODO: Rather than pass executor, use self.hosts for
  #       server addressing
  def requestExecution(self, Server):
    for i in self.actionsets[0]:
      # Will eventually not require client hostname,
      #   as the server will determine this itself.
      Server.addCommand(i[1], "rakep")
      Server.runCommand()
