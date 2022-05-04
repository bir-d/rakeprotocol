class Client: 
  def __init__(self, rakeData):
    print("[rake.p] Initialised Python rake client.\n")
    self.port         = rakeData.port
    self.hosts        = rakeData.hosts
    self.actionsets   = rakeData.actionsets

  # is not able to see if the server is busy
  # simply a naive execution script
  def requestExecution(self, Executor):
    for i in self.actionsets[0]:
      Executor.addCommand(i[1], "rakep")
      Executor.runCommand()
