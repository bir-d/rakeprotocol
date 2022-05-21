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

If you receive FAILURE_RSP, the header follows the same 62 byte length, so read the body for any stderr, report, and terminate.
If you receive SUCCESS_RSP, the header follows this format:
* 2 byte `code`
* 3 byte `response type`, one or more of (spaces replace unset flags)
    * STDOUTP = S
    * INCFILE = I
    * FILETRN = F
* The other 56 bytes are still the padded length of the payload to be received.

S should be be first to be received, and contains the standard output of the command to be reported and stored (`S `)
If I is set (`SI `), receive and parse another header, which should contain a payload of a file to be received. Each file "transmission" will have F set as well.
Receive F packets (` IF`) until I is no longer set. (`  F`)

Each file packet is proceeded by a filename packet, designated by having all three flags set (`SIF`)

##### A quick example
(`SI `) -- This is the standard output. Report it. We can see that `I` is set, lets recv the next packet...
(`SIF`) -- This is a filename. Store it and receive the file upcoming...
(` IF`) -- Here is the file content for the previously received filename. `I` is still set. Lets keep receiving.
(`SIF`) -- As expected, another filename.
(`  F`) -- Here is the file content. `I` is not set, so that is the last file we need to receive.

Store the standard output and any files, if any, on the client folder.


### Server


## Execution

> a 'walk-through' of the execution sequence employed to compile and link an multi-file program, and

## Results

> the conditions under which remote compilation and linking appears to perform better (faster) than just using your local machine.

