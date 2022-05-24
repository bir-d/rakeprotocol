# Protocol
The basis of the protocol is a fixed size, 64 byte UTF-8 header sent between the client and server, and a variable length "payload", which size is indicated in the header.

The first two bytes of the header is the "code", one of:
   * DISCONN_MSG     = "!D"
	   - Client: sends to server once it has finished with it.
	   - Server: cleans up data structures for client
   * COMMAND_MSG     = "!C"
	   - Client: Sends this with a payload of command to execute.
	   - Server: Executes the payload from this packet, and captures exit state, stdout, stderr, and any generated files, and passes it off to the client
   * REQUEST_MSG     = "!R" 
	   - Client: Sends this to indicate to the server that it will need to receive files
	   - Server: Prepares to receive files from the client
   * SUCCEED_RSP     = "!S"
	   - Client: Indicates success, should keep processing the packet and rakefile
	   - Server: Sends this to indicate execution was successful
   * FAILURE_RSP     = "!F"
	   - Client: Indicates failure, receive payload as stderr and terminate
	   - Server: Sends this to indicate execution was unsuccessful
   * EXECUTE_GET     = "!E"
	   - Client: Sends this to get current amount of requests server is servicing
	   - Server: Sends active thread count to client.
	   
The next three bytes are "options", only used on successful execution responses. These are positionally sensitive, and are either set, or unset(replaced with a space):
* STDOUTP         = "S"
* INCFILE         = "I"
* FILETRN         = "F"

* S is set if the packet contains standard output
* I is set if output files are to be sent back to the client, and for it to prepare to receive a filestream
* F is set only on filestream packets

Finally, the next bytes indicate the length of the payload, and the rest of the header is padded out to 64 bytes total with spaces.

## Filestream protocol
Filestreams are just multiple files to be sent and received by a client and server. Each filestream consists of a metadata packet, and for each file, packets for filename, filesize, and for transfer confirmation. Filestreams use one of these codes in replacement of the first two bytes of the "options", with the last byte of options set to F to indicate that it is a filestream packet.

    FILENAME    = "!N"
    FILETRAN    = "!T"
    FILESIZE    = "!Z"
As an example, the client receiving a filestream might ask for the filename of one of the files its receiving by sending off (padded to 64 bytes) `!N`, and get this back:
	Header: `!S!NF7[57 spaces]`
	Payload: `Dog.txt`
	
An example exchange between client and server, with the client sending a filestream of dog.txt(34 bytes) and feline.txt(88 bytes) to the server, as requirements.

```
|--------!R--------->| Indicate requirements
|------!SSIF2------->| Client sends metadata packet showing 2 files to be sent

|<-------!N----------| Server asks for name of first file
|------!S!N7-------->| Client sends 64 byte header indicating 7 byte filename payload
|------dog.txt------>| Client sents payload of filename
|<-------!Z----------| Server asks for filesize of first file
|------!S!Z2-------->| Client sends 64 byte header indicating 2 byte file size payload
|--------34--------->| Client sents payload of file size
|<-------!T----------| Server requests transmission to start
|-The dog or domes..>| Client begins transfer of file. Server receives based on filesize and saves to file based on received filename

|<-------!N----------| Server asks for name of second file
|------!S!N10------->| Client sends 64 byte header indicating 10 byte filename payload
|------feline.txt--->| Client sents payload of filename
|<-------!Z----------| Server asks for filesize of second file
|------!S!Z2-------->| Client sends 64 byte header indicating 2 byte file size payload
|--------88--------->| Client sents payload of file size
|<-------!T----------| Server requests transmission to start
|-Feline may refer..>| Client begins transfer of file. Server receives based on filesize and saves to file based on received filename

```

# Execution Sequence
Test case: One client, two servers
```PORT  = 12345
HOSTS = host1 host2

actionset1:
	remote-cc -c func1.c
		requires func1.c
	remote-cc -c func2.c
		requires func2.c

actionset2:
	remote-cc -c program2.c
		requires program2.c

actionset3:
	remote-cc -o program2 program2.o func1.o func2.o
		requires program2.o func1.o func2.o
```

* Client parses the rake file successfully
* Client looks at the first actionset, and for each action:
	- `remote-cc -c func1.c
		requires func1.c`
		- Polls host1 and host2 by sending `!E`. Neither are busy, so picks host1.
		- Sees func1.c is required for action
		- Sends `!R` to server, then sends filestream of func1.c
		- Sends `!C` to server, with payload `remote-cc -c func1.c`
		- 		- Server executes command, and detects output to send back
		- Doesnt wait for response, but adds host1's socket to a watchlist, and increments the count of commands sent by one
	- `remote-cc -c func2.c requires func2.c` 
		+ Polls host1 and 2. 1 has one more active thread than 2, so we pick 2
		+ Sees func2.c is required for action
		- Sends `!R` to server, then sends filestream of func2.c
		- Sends `!C` to server, with payload `remote-cc -c func2.c
		- Server executes command, and detects output to send back
		- Doesnt wait for response, but adds host2's socket to a watchlist, and increments the count of commands sent by one
	* Until commands sent = 0
		- select() our watchlist, see 1 is ready
			+ Get header
			+ `!SSI 0[padding]`
			+ Get payload
				* Nothing, no stdout
			+ I is set, so we pass the socket off to the filestream handler and receive func1.0
		- select() our watchlist, see 2 is ready
			+ Get header
			+ `!SSI 0[padding]`
			+ Get payload
				* Nothing, no stdout
			+ I is set, so we pass the socket off to the filestream handler and receive func2.0
			
	Repeat this process for actionsets 2 and 3.
	
# Remote compilation performace
Remote compilation performs better under these conditions:
* The server has a faster compilation time than the client. (Perhaps the client is a small, embedded device, and the server is a proper workstation)
* This performance difference is larger than the performance penalty incurred by sending the files over a network. (If the network is slow enough, it can simply take more time to transfer requirements than any time saved by using a better CPU)

Additional considerations include that large complex compilations can be spread across an arbitrary amount of servers, so a huge task which can be executed in parallel would perform better remotely than locally.