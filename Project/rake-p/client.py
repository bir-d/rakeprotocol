from parser import Rake

if __name__ == '__main__':
  print("[rake.p] Initialised Python rake client.\n")
  R = Rake("Project/Rakefile.1")
  R.printRakeDetails()
  