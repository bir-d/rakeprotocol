import os 

# Only supports local execution.
# Detailed implementation consider using `exec` instead
def simpleExecuteAll(actionsetNum, actionset):
  print("[rake.p] Executing actionset", actionsetNum, " commands...", sep="" )
  for action in actionset:
    command = action[1]
    os.system(command)