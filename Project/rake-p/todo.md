# Todo 05/05

1. Thursday 5/5
  - Fix the small things from late-night code. [jamie]
  - Drafting a "whitepaper" of how the communication works. [cormac]

2. Friday 6/5   [incomplete: waiting on todays work]
  - Extend the code to be more defined in relation to client-server communication
    - Neccessary for later where communication is more important
  - Prepare code for seperation of tasks, rather than one file.
  - As socket is file, make so:
    - client writes to dummy socket
    - server monitors text file and reads stuff
    - replace dummy file descriptor with a socket 

---

## Cormac Logic Brain Worm

Problem: Must write logic where client must execute remote command that it then finds a remote host that can accept this command.

1. For each command, poll server: ask "are you busy?/how many items in your queue?"
  - Makes a decision based on the result of this result.
  - Pros:
    - Robust
  - Cons:
    - Polls EVERY host EVERY time for a command
  - Probably the one to go.
  - Only problem where many many clients exist.
    - Probably a limit of 1024, as select() can only monitor 1024 file descriptors
    - Might be mentioned as an alternative to multithreading
      - Doesnt handle all the logic however
    - More research needed into the function of select() system call.
  
2. Client tracks remote it knows about. [PROBABLY DOESNT WORK]
  - When it sends a command, marks the host as busy
  - Stays busy until the client recieves a result from the host
  - Question: Does this require a server set up that does NOT use a queue?
    - Maybe, but can probably hold server commands in queue for each time sent
    - Where multiple clients make requests to multiple servers, number may be incorrect
    - Cannot rely on client for accurate information on what server is doing
      - May mean logic of (2) cannot be done

- If (2) not possible, then the main problem is how to manage issue of frequent polling inefficiency
  - Example: One server, multiple clients
    - Assume command takes 5 seconds
    - First client gets execution
    - Other clients will then continue to ask "are you busy?" 
    - This is annoying.
  
- How often should a client ask?
  - Clients not aware of other clients.
  - Looking to 802.3 Protocol (Ethernet)
    - QUESTION::If two clients send server requests, do they collide?
      - No, as they are not using the same connection to the server.
  - If client finds ALL servers busy, will it poll ALL of them instantly?
    - Will it poll them each given time period (eg. 5 second intervals)?
    - Will it base a waiting time on previous waiting time taken?
      - Binary Exponential Back-Off: Wait twice amount of time as last time.

- ASYNCH :: If all commands in an actionset execute simultaneously: 
  - Inevitably a case exists where, first server hit with 5 different polls, second server hit with 4 polls etc...
  - In this case, polling halts where server replies that it isnt busy
  - While the commands are asynch, the polling requests should 'synchronus'
    - i.e. First server polled before the second is polled
  - Means that this issue arise, as only each server polled until availble server is found.
  - PROBLEM :: Can server execute multiple things?
    - Probably not
  - Going to probably smash every server with polls
    - Chris implies optimisation requires a command queue system for the server
      - "...commands sent have associated cost, equal to the number of commands currently in its queue"
      - Client cannot determine server with lowest cost unless it asks each server what that cost is.
      - No way to optimise this without client polling EVERY server for EVERY command in its queue
      - You cant skip this, unless you know there is only one client (impossible)
    - Server then holds this cost, sending it to the client on poll request (cost = length of queue)
  
  

## Notes

- Abstraction: Client sends command to server, server executes/returns result
- Main work focuses on this interaction
- How does server 'know' what is is recieving?
  - Is it a command?
  - Is it a requirement?
  - Is it waiting for requirements?
  - Is it receiveing those files
  
- Once server executes command and gets results, what are the results?
  - Is it a file?
  - Is it a error? 
  - Is it stdout (should be returned regardless)?
  - Is it stderr?
  
- Client should be able to recognise if it recieved an error
  - Where an error occurs in actionset, the following sets must halt execution
    - Actionsets              ==    Sequential
    - Commands of Actionsets  ==    Asynchronous
  - Where a file is received, the client needs logic for handling these.
    - Maybe not true: running on your PC with different environments?

- ASSUMPTION 1 :: Only remote commands need requirements, not local? 
  - NO:: Local needs requirements for some execution.
    - Maybe have to pull logic from the server into the client?
  - Requirements for local may need some way to find directories they are stored.
    - Opens potential logic needs to determine if relative path or absolute
    - How are these local requirements handled? 
      - Are they sent to localhost server? (Assumption 2)
      - Parser must answer "where is this requirement im sending?"
  - Potentially there must be requirement finding functionality
    - Where requirements are searched for on client computers
    - Handle when requirements are not found.
    - Maybe requirements are "current directory-relative paths"?

- ASSUMPTION 2 :: Client and Server both listening on localhost
  - Client does not 'execute' anything itself, it only executes on server.
  - Run client, parses rake, 
    - if command remote: sends to any non-localhost
    - if not: sends to localhost
  - Server only sees command, executes it, and returns results to client.
  - CLIENT NEVER EXECUTES COMMANDS ITSELF, BUT COMMAND EXECUTES ON LOCALHOST SERVER

- ASSUMPTION 3 :: Remote commands can use localhost too
  - Where remote execution occurs, localhost usable as execution as well(?)
  - LOCAL commands cannot be execute on REMOTE hosts
  - This assumption only holds if assumption 2 is true.

## Execution `executor.py`
- Fix logging/directories to be client based, rather than server based
  - Rather than `rakeserver_tmp` should be `rakep_tmp` (same convention for log)
- Handle errors in try:except loops to be more precise
  - OSError and subprocess errors are too broad, and imprecise
  - Should be able to know whether file exists, doesn't exist, is inaccessible etc
  - Want to know whether appending is possible.
  - Differentiating between an error that functionality can continue, and where an error is not able to permit further execution (such as lacking permissions for file/anything that means it does not already exist).

