# CITS3002 Computer Networks

### Practical project 2022

**(due 5pm Fri 20th May - end of week 11)**

See also: [**Clarifications**](https://teaching.csse.uwa.edu.au/units/CITS3002/project2022/clarifications.php)

**The goal** of the project is to develop a internetworked application that compiles and links C programs across different computers connected using internet protocols.

By successfully completing the project, you will have a greater understanding of the standard TCP and IP protocols, know how to use programming languages' interfaces to internet protocols, and have developed a simple application-layer protocol for the exchange of queries, responses, and files.

#### Outline

Modern desktop and laptop computer systems, even tablets, boast multi-core processors that permit multiple processes to execute on distinct cores, simultaneously. Resource intensive processes can be locked to a particular core to reduce interference and further improve performance. 

However, even with 4 or 8 cores, some tasks can still benefit from greater performance - [compiling the Linux kernel source code](https://openbenchmarking.org/test/pts/build-linux-kernel&eval=693e2017227780b46fd0a55912b67c1b7e5ca564) or large million-line C++ projects can still take tens of minutes to compile and link.

- Download and expand the file [building.zip](https://teaching.csse.uwa.edu.au/units/CITS3002/project2022/building.zip) into a new directory.

Its *Makefile* **demonstrates how a C program**, requiring some external functions, **can be compiled and linked in three different ways**. 

- Ensure that you completely understand what this example demonstrates. 

Other than their role in demonstrating possible ways of building a program, **these files have nothing else to do with the project** (they are not a 'big hint').

- Consider the following textfile that looks *roughly* like a standard *Makefile* (but is not a *Makefile*). As our project involves **R**emote compilation, we'll refer to this file as a *Rakefile*.

```c
# A typical Rakefile

PORT  = 6238
HOSTS = hostname1 hostname2 hostname3:6333

actionset1:
    echo starting actionset1
    remote-cc [optional-flags] -c program.c
        requires program.c program.h allfunctions.h
    remote-cc [optional-flags] -c square.c
        requires square.c allfunctions.h
    remote-cc [optional-flags] -c cube.c
        requires cube.c allfunctions.h

actionset2:
    echo starting actionset2
    remote-cc [optional-flags] -o program program.o square.o cube.o
        requires program.o square.o cube.o
```



**De-stressing note -** this is a systems-focused networking project - it is not assessing your parsing of a (simple) textfile. 

You may assume that any *Rakefile* will be syntactically correct and, so, you won't need to rigorously parse them or report any syntax errors. 

Everything in a *Rakefile* may be read and stored from top-to-bottom, left-to-right, with no recursion or dependencies to be resolved.

- **Hint:** parse the whole *Rakefile* and store its information in your client's data-structures before commencing the execution of processes. Some *Rakefile*s and a program to generate them for tens or hundreds of C source files will be provided.

In the example above, **the names of the remote hosts that will perform the compilation and linking of C files are provided** - there will **always be at least one hostname which (for testing) may be *localhost*.** 

*hostname3* is also followed by an integer port-number, indicating that its server (named *rakeserver*) will be listening on a port other than the default (6238).

Lines commencing (indented) with a single tab-character are *actions* (commands). An action commencing with the string *"remote-"* is to be executed on one of the remote hosts. Actions without that leading string are to be executed on the client's host.

Lines commencing (indented) with two tab-characters indicate any additional files required to successfully execute the previous line's action. As the files will be located on the client's host, they must first be sent to the chosen remote host.

Note that some remote hosts may have specific resources (files) that are not present on the client's host (for example, a library under a proprietary license and, hence, it cannot be distributed). Those resources need not (cannot) be first sent to the remote host.

As in the example above, a *Rakefile* may have multiple numbered sets of actions. All of the actions in *actionset1* should be executed simultaneously (in parallel), usually on remote hosts, and all actions in *actionset1* must have executed successfully before any actions in *actionset2* are commenced.

If any command in an *actionset* fails then the next *actionset* is not commenced (**Hint -** compilations may fail, and their errors should be reported).

While you can assume that all remote hosts have the same architecture and operating system as the local (client's) computer, they may each have a very different performance and available resources. 

Before commencing the execution of each command in an *actionset*, each remote host should be queried to determine how much it will 'cost' to execute a command. 

- The remote host (first) returning the lowest cost is the one on which the command will be executed. 
- The actual costs reported by each remote server are, of course, not real and have no units, but should reflect the number of other commands currently managed by its *rakeserver*, and may include a cost for linking with a hosted/unique/proprietary library.



#### Requirements

1. your project will be developed and marked on either Linux or macOS - typically the RHEL distribution in CSSE labs, Ubuntu Linux (natively or within Microsoft's WSL-1 or 2), or macOS Monterey or Big Sur. You only need to develop on *one* platform.

2. your project will consist of *client* and *server* programs developed in standard C99 (or C11, or C17), and Python v3.6 (or later). 

3. your project's *single* server program, named *rakeserver*, will be developed in *either* C or Python. The choice is up to you.

4. you will develop *two* distinct client programs - one in C named *rake-c* and one in Python named *rake-p*. Each client should simply attempt to read from a file named *Rakefile* in the current working directory.

5. your project will be capable of executing multiple instances of your server program on distict (physical) computers connected using internet protocols, and each of your client programs on the computer 'in front of you'.

6. you should employ the core networking functions (classes, methods, libraries,...) of each programming language and not employ specific 3rd-party frameworks or resources.


The learning in this project comes from developing an understanding of how an operating system's system calls, and programming languages' standard libraries, may be used to address a task. There is far less learning (or a very different type of learning) required in just combining existing libraries and modules to solve a task.



#### Project deadline and submission requirements

- The project contributes **40%** of your mark in CITS3002 this year.
- By **5PM Friday 20th May** (end of week 11) submit via [cssubmit](https://secure.csse.uwa.edu.au/run/cssubmit) your team's project submission. Only one team member needs to submit the work.
- Submit your project as a single archive file, such as a tar or zip file. Your archive file should contain:
  - a single textfile named *team.txt* containing the names and student number of your project's team members (even if completed individually), and the operating system used (state just Linux or macOS);
  - three subdirectories of source-code named *rakeserver*, *rake-c*, and *rake-p*; and
  - a single *PDF* file named *report.pdf*.
- Your project report (a PDF file) should be no more than 3 A4 pages long, and describe (ideally with diagrams and examples):
  - the protocol you have designed and developed for all communication between your client and server programs,
  - a 'walk-through' of the execution sequence employed to compile and link an multi-file program, and
  - the conditions under which remote compilation and linking appears to perform better (faster) than just using your local machine.

#### Working individually or in teams of 2 or 3

The project may to be undertaken individually or in teams of 2 or 3 students (1,2,3, but not 4). 

The motivation for working in small teams is to enhance communication skills amongst students, and to enable you to attempt a project considered of greater difficulty than would normally be reasonable for the time available. 

It is anticipated that this project will require **20-30 hours** of study by each member of a 3-person team. 

The project is worth **40%** of your mark in CITS3002 this year, and the distribution of marks within your team (such as one-third each) must be agreed to by all members of your team. 

Only one team member needs submit files using [cssubmit](https://secure.csse.uwa.edu.au/run/cssubmit). Ensure that all students' names and student numbers appear in all submitted materials. Anyone needing to find a project partner should post their information to [*help3002*](https://secure.csse.uwa.edu.au/run/help3002?year=2022&opt=B142), or send a personal message (PM) via *help3002* to other students also looking for a project partner. 

#### Clarifications

Please post requests for clarification about any aspect of the project to [*help3002*](https://secure.csse.uwa.edu.au/run/help3002?year=2022&opt=B223) so that all students may remain equally informed.
Clarifications will be also added to the [**project clarifications**](https://teaching.csse.uwa.edu.au/units/CITS3002/project2022/clarifications.php) webpage.

Good luck,

Chris McDonald, April 2022.