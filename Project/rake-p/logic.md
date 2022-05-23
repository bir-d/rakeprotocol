* Get List of all servers
* Get sockets for each. and register them all.

loop start
* For each cmd in the action set, do cmd handling
* select() and wait for responses
* For each response, response handling
loop end

# cmd handling
* Poll each server, send command over to lowest cost.

# response handling
* Exit code != 0, report and stop execution
* need to receive files if any


# Unblocking `send`
* need to decouple receiving from the send command.
    * commmand
    * Execute get
    * Request (?)
        * SENDS REQUIREMENTS
    * Disconn (nothing to receive)

# add an ID to distinguish between what we are watching


todo:
decouple recv and send entirely -- generic funcs for both.
* This does need the codes to actually be sent back and forth in the header. 
* Will this need an ID to be echoed by the server? Or is there a better way for the  client to know which response it is in reference to
    * One way to rectify would be to simply make a new connection per command.
        * make sockets during polling stage, select until all results back, send command to lowest cost, 
        ... the only way for this to work is to have blocking connection for polling, and then non blocking for commands. 

        SELECT FOR POLLING. ONCE ALL POLLED, CLOSE ALL SOCKETS EXCEPT FOR THE ONE OF LOWEST COST. REGISTER THE REMAINING ONE TO BE SELECTED AT THE START OF THE NEXT LOGIC LOOP AND HANDLE.