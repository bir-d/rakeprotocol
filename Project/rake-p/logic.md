* Get List of all servers
* Get sockets for each.
* For each cmd in the action set, do cmd handling, add socket used to fdset
* select() and wait for responses
* For each response, response handling
loop

# cmd handling
* Poll each server, send command over to lowest cost.

# response handling
* Exit code != 0, report and stop execution
* need to receive files if any
