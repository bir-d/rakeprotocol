# Client outline

## Parse rakefile

## Main logic loop
### Sending off commands
* For each actionset
	- For each action
		+ Determine location
			* If local, location is just localhost:PORT
			* If remote:
				- Poll each server for cost, pick the lowest cost server
					+ Open a blocking socket to each server
					+ Send `!E`
					+ Receive 64 byte header
						* First two bytes, should be !E.
						* Next 62 bytes, remove padding and should be length of payload
						* Receive length bytes from socket, make int
					+ Close socket
		+ Open non blocking socket to determined server
		+ Check requirements. If any:
			* Send server `!R`
			* Send server requirements via filestream protocol
		+ Send command:
			* Send server:  
				- Header: `!E` + Length of payload + padding (out to 64 bytes)
				- Payload: Command you want run
				- Example:  
					+ Header: `!E8[56 spaces]`
					+ Payload: `cat file`
		+ Add the socket you used to a fdset.
		+ Keep track of how many commands you've sent. Because now we must receive that many commands back.
		
### Receiving output
* Until you receive and process responses equal to the commands you sent:  
	- Select() the prepared fdset to get the sockets which are ready.
	- For each socket:
		+ Receive a 64 byte header
		+ First two bytes: status
			* `!S` Success
			* `!F` Failure
				- On failure, read the rest of the header (should be 62 bytes) to get the payload length (once padding is removed). Receive the payload, which should be stderr of the command that failed. Report the stderr and exit.
		+ Next three bytes: options
			* `S`: Standard output
				- If this is set, receive the payload (which is stdout), and report it to the user
			* `I`: Incoming files
				- If this is set, pass the socket to a filestream handler **after** receiving and reporting any payload
			* `F`: Filestream packet
				- Usually empty (replaced with a space) at this point
				
		+ Until end of header (next 59 bytes with a 64 byte header):
			* Length of payload (Usually `stdout`)
		+ Once this handing is done, remove the socket used from the fdset and decrease the count of waiting responses by one.
			
		


## Filestream Protocol
### Sending
- Send metadata packet
	+ Success code, all options set, length of payload, padded out to 64 bytes
	+ Then the payload, which is just number of files you are sending (So if you are sending 56 files, the payload is `56`, length of payload is just `2`)
- Then for each file
	+ Wait for filename packet
		* Will just be `!N` padded to 64 bytes
		+ Send filename
			* Header is status code(Probably !S) + !N + filestream (F)+ payload length + padding
			* Payload is the filename of the file you are sending right now
			* Example
				- Header: `!S!NF7[57 spaces]`
				- Payload: `Dog.txt`
	+ Wait for filesize packet
		* Just `!Z` padded
		* Send filesize
			- Header: status code + !Z + F + Length
			- Payload: number of bytes the file is.
			- Example
				+ Header: `!S!Z10[54 spaces]`
				+ payload: `6487635634`
	+ Wait for file transfer request
		* Just `!T`
		* Then start sending the file over the socket. The server knows how many bytes to receive.
		
### Receiving
- Receive metadata packet (64 bytes padded)
	+ Header = `!SSIF`+ payload length
	+ payload = Number of files to receive
- For each file to be received:
	+ Request filename (`!N` padded)
		* Response (64 byte padded):
			- Header: `!S!NF`+ payload length
			- Payload: Filename
	+ Request filesize (`!Z` padded)
		* Response (64 byte padded):
			- Header: `!S!ZF`+ payload length
			- Payload: Filesize
	+ Request file transfer (`!T` padded)
		* Read `filesize` bytes from socket. Save this data to a new file called `filename`
		

## Suggested path
* Write Parser [x]
* Write Send command []
	- Socket, code, options, padding, payload
		+ Assemble packet to send
			* First two bytes, code
			* Next three bytes, options (if not null)
			* Tack on length of payload
			* Tack on padding, calculated by the length of the above minus the header length (64 by default)
		+ Send packet to socket
* Write receive response command []
	- Socket
		+ Receives the header (64 bytes) from socket.
		+ Checks code (first two bytes)
			* !E, get payload length immediately as the 62 bytes of the header which aren't the code. Receive the payload next, convert to int and return.
			* !S
				- Checks options (next three bytes)
				- If S set, standard output report
				- If I set, pass off to filestream after report
				- F should not be set since filestream packets should not be here.
			* !F
				- Handle failure, payload length comes immediately like `!E`, report payload as stderr and exit.
* Write logic loop []
	- For actionset
		+ for action in actionset
			+ determine location
				* implement polling
			+ send command to location
			+ add socket to fdloop, add one to command counter
		+ While command counter > 0
			* select() fdset
			* for readable socket
				- pass off to receive response command
				- reduce response counter by one
				- remove socket off fdset.

You can test here, with rakefiles which do not have requirements.

* Implement Filestream send []

Can test here, as long as no output generated

* Implement FIlestream receive []


And done!
 