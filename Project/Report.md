# Report

> Your project report (a PDF file) should be no more than 3 A4 pages long, and describe (ideally with diagrams and examples):


## Protocol

> the protocol you have designed and developed for all communication between your client and server programs,
### Client
First, we parse the rakefile. Then, we go through each actionset. For each command in the action set, we follow these steps:
* Check if any watched servers have a response ready, then handle it.
* Poll all unwatched servers for cost, and pick the one with the lowest cost. In doing this, create a socket for each server we are polling, and close all which are not the "lowest cost"
* Send the requirements, if any, to this server.
* Send the command to the server.
* Register this server (socket) to be watched.

#### Sending commands
Each command sent has the following structure:
* 64 Bytes of header, consisting of:
    * First two bytes: a `code`
        * A code is one of the following:
                * DISCONN_MSG     = "!D"
                * COMMAND_MSG     = "!C"
                * REQUEST_MSG     = "!R" 
                * SUCCEED_RSP     = "!S"
                * FAILURE_RSP     = "!F"
                * EXECUTE_GET     = "!E"
    * The rest of the header is reserved for the length of the payload.
* The payload, who's length is decided by the header. 
#### Handling Responses
First, read the first two bytes for the code. Then read the next 62 bytes in (header - `code` length == 64 - 2 == 62). The length is padded by spaces if it does not take up the whole 62 byte allotment. Receive the number of bytes provided by the header. For the client, you are concerned about these codes:
* SUCCEED_RSP     = "!S"
* FAILURE_RSP     = "!F"
* EXECUTE_GET     = "!E"

If you receive FAILURE_RSP, the header follows the same 62 byte length, so read the body for any stderr, report, and terminate.
If you receive SUCCESS_RSP, the header follows this format:
* 2 byte `code`
* 3 byte `response type`, one or more of (spaces replace unset flags)
    * STDOUTP = S
    * INCFILE = I
    * FILETRN = F
* The other 56 bytes are still the padded length of the payload to be received.

S should be be first to be received, and contains the standard output of the command to be reported and stored (`S `)
If I is set as well (`SI `), there are incoming files to be received, and the socket should be passed off to a filestream handler.

#### Handling Filestreams
Filestreams are just sequences of files being sent. Each file takes the form of one metadata packet and one or more content packets. 
Each filestream begins with a filestream packet, which indicates the number of files which need to be received instead of a payload length, and does not have a payload. Additionally, it is designated by having all three flags set.
For each file that needs to be received, the client requests a filename, then requests the file transfer to start. This repeats until there are no more files to receive. These requests occupy these codes:

* FILENAME = !N
* FILETRAN = !T

In general, filestream packets (aside from the metadata packet) don't use STDOUTP or INCFILE, so those two bytes are used for FILENAME or FILETRAN.

##### A quick example
(`!SSI `) -- This is the standard output. Report it. We can see that `I` is set, meaning that there are incoming files. Lets receive the next 64 byte packet 
(`!SSIF2`) -- This marks the start of the filestream. We can see that 2 files are to be received. We send off a filename req packet and receive:
(`!S!NF10`, `output.txt`) -- We receive a 10 byte filename, `output.txt`. We send off a filetran request and keep reading until we read 0, and save that data to a file. We know from the metadata packet we have one more file to receive, so we repeat the process once more.

Store the standard output and any files, if any, on the client folder.


### Server


## Execution

> a 'walk-through' of the execution sequence employed to compile and link an multi-file program, and

## Results

> the conditions under which remote compilation and linking appears to perform better (faster) than just using your local machine.

