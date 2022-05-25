// Dear Marker,
//
// The C client is in a non-functioning condition.
// I have attempted to show a flow of logic that
// would allow the client to be used... if of course
// it worked. 
//
// We had got a response from the server, but it was
// not able to execute anything, as a result, I attempted 
// building this functionality, losing the original 
// connection we had established in the way.
//
// Regretfully,
// Jamie & Cormac

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <errno.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <netdb.h>
#include <sys/socket.h>
#include <arpa/inet.h>

// -----------------------------------------------------------------------------
// COMMUNICATION DEFINITIONS
// -----------------------------------------------------------------------------

// Client Parameters
#define MAX_COMMANDS 256        // max number of commands in actionset
#define MAX_SERVERS 256         // max number of host servers
#define MAX_ACTIONSETS 256      // max number of actionsets in rakefile
#define MAX_NAME_LEN 64         // max length of a name

// Communication Protocol
#define HEADER_LEN 64
#define CODE_LEN 2
#define RESPONSE_LEN 3
#define MAX_LEN 1024
#define FORMAT = "utf-8"

// Message Codes 
#define DISCONN_MSG "!D"
#define COMMAND_MSG "!C"
#define REQUEST_MSG "!R"
#define EXECUTE_GET "!E"

// Response Types
#define SUCCEED_RSP "!S"
#define FAILURE_RSP "!F"

// File Options
#define STDOUTP "S"
#define INCFILE "I"
#define FILETRN "F"

// File Transfer Types
#define FILENAME "!N"
#define FILETRAN "!T"
#define FILESIZE "!Z"


// -----------------------------------------------------------------------------
// DATA STRUCTURES
// -----------------------------------------------------------------------------

typedef struct COMMAND
{
    char *location[MAX_NAME_LEN];    // remote/local
    char *command;     // command to execute
    char *requires;    // files needed for execution
} COMMAND;

typedef struct ACTIONSET
{
    int index;                      // actionset number
    int num_actions;                // number of actions in actionset
    COMMAND commands[MAX_COMMANDS]; // array of commands
} ACTIONSET;

typedef struct SERVER
{
    char full_host[MAX_NAME_LEN];      
    char host[MAX_NAME_LEN];   
    int port;
    bool local;
    int sockfd;
    int cost;
} SERVER;

typedef struct HEADER
{
    char code[CODE_LEN];
    char flags[RESPONSE_LEN];
    char length[HEADER_LEN];
} HEADER;


// -----------------------------------------------------------------------------
// GLOBAL VARIABLES
// -----------------------------------------------------------------------------

ACTIONSET   actionsets[MAX_COMMANDS];
SERVER      servers[MAX_SERVERS];
int         numServers = 0;
int         server_index_cost_array[MAX_SERVERS];

HEADER EXEC_COST_HEADER = {
        .code = EXECUTE_GET,
        .flags = "",
        .length = ""
};


// -----------------------------------------------------------------------------
// PARSING
// -----------------------------------------------------------------------------

// Read in the rakefile and store the actionsets in the actionset array
int read_rakefile(FILE *rake_fp)
{
    char linebuf[256];
    int actionset_index = -1;
    int server_index    = -1;
    int command_index   = -1;
    int requires_index  = -1;
    int default_port    = -1;

    printf("[r.c] reading rakefile...\n");

    // read file line by line
    while (fgets(linebuf, 512, rake_fp) != NULL)
    {
        linebuf[strlen(linebuf) - 1] = '\0';
        // ignore line if comment, newline, or empty
        if (linebuf[0] == '#' || linebuf[0] == '\n' || linebuf[0] == '\r')
            continue;
        // finds default port number
        else if (strncmp(linebuf, "PORT", strlen("PORT")) == 0)
        {
            default_port = atoi(linebuf + strlen("PORT = "));
        }
        // finds host servers and stores in server array
        else if (strncmp(linebuf, "HOST", strlen("HOST")) == 0)
        {
            char *token = strtok(linebuf + strlen("HOSTS = "), " ");
            while (token != NULL)
            {
                server_index++;
                numServers++;
                strcpy(servers[server_index].full_host, token);
                token = strtok(NULL, " ");
                if (strchr(servers[server_index].full_host, ':') == NULL)
                {
                    // combine server host with default port
                    char port_str[10];
                    sprintf(port_str, "%d", default_port);
                    servers[server_index].port = default_port;
                    strcpy(servers[server_index].host, servers[server_index].full_host);
                    strcat(servers[server_index].full_host, ":");
                    strcat(servers[server_index].full_host,  port_str);
                }
                else if (strchr(servers[server_index].full_host, ':') != NULL)
                {
                    // split server host into host and port
                    char *host_token = strtok(servers[server_index].full_host, ":");
                    char *port_token = strtok(NULL, ":");
                    sprintf(servers[server_index].host, "%s", host_token);
                    sprintf(servers[server_index].full_host, "%s", host_token);
                    sprintf(servers[server_index].full_host, "%s:%s", servers[server_index].full_host, port_token);
                    servers[server_index].port = atoi(port_token);
                }
                if (strcmp(servers[server_index].host, "localhost") == 0 || strcmp(servers[server_index].host, "127.0.0.1") == 0)
                {
                    servers[server_index].local = true;
                }
                else
                {
                    servers[server_index].local = false;
                }
            }
        }
        else if (strncmp(linebuf, "actionset", strlen("actionset")) == 0)
        {
            actionset_index++;
            command_index = 0;
            requires_index = 0;
        }
        // finds requirements of lines
        else if (linebuf[0] == '\t')
        {
            if (linebuf[1] == '\t'){

                // // split line on space and store in array
                // char *token = strtok(linebuf + 2 + strlen("requires"), " ");
                
                // while (token != NULL)
                // {
                //     // strcpy(actionsets[actionset_index].commands[command_index].requires[requires_index], token);
                //     token = strtok(NULL, " ");
                //     requires_index++;
                // }
            }
            else 
            {
                printf("CMD");

                actionsets[actionset_index].num_actions++;

                // determines whether line is remote or locally executed
                if (strncmp(linebuf, "\tremote-", 8) == 0)
                {
                    char *comm;
                    strncpy(comm, linebuf + strlen("\tremote-"),  strlen(linebuf) - strlen("\tremote-"));


                    COMMAND command = {
                        .location = "remote",
                        .command = comm};
                    actionsets[actionset_index].commands[command_index] = command;

                }
                else
                {
                    char *comm;
                    strncpy(comm, linebuf + strlen("\t"), strlen(linebuf) - strlen("\t"));

                    COMMAND command = {
                        .location = "local",
                        .command = comm
                    };
                    actionsets[actionset_index].commands[command_index] = command;
                }
                command_index++;
            }
        }
    }
    printf("[r.c] done reading rakefile\n");
    return EXIT_SUCCESS;
}


// -----------------------------------------------------------------------------
// SOCKETRY
// -----------------------------------------------------------------------------

// Establish connection to server on host and port given.
int connect_socket(char *host, int port)
{
    printf("\n[r.c] Connecting to '%s:%d'...\n", host, port);

    int sockfd = 0, n = 0;
    struct sockaddr_in serv_addr;
    char recvBuff[1024];

    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0)
    {
        printf("\n[r.c] Error: Could not create socket \n");
        return 1;
    }

    memset(&serv_addr, '0', sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);

    if (inet_pton(AF_INET, host, &serv_addr.sin_addr) <= 0)
    {
        printf("\n[r.c] Error: inet_pton error occured\n");
        return -1;
    }

    if (connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0)
    {
        printf("\n[r.c] Error: Connect Failed \n");
        return -1;
    }

    printf("[r.c] Sucessfully connected.\n");

    return sockfd;
}

int connect_server(SERVER server) {
    server.sockfd = connect_socket(server.host, server.port);
    return server.sockfd;
}


// -----------------------------------------------------------------------------
// RECEIVING FUNCTIONS
// -----------------------------------------------------------------------------

// Sends message header to the socket.
char* receive_header(int sockfd, bool uses_flags)
{
    if (sockfd < 0)
    {
        printf("[r.c] Error: Socket is not open.\n");
        return "-1";
    }
    char *code;
    char *val;
    char flags[RESPONSE_LEN];

    char *headBuff;
    char *recvBuff;

    // READING HEADER
    read(sockfd, headBuff, HEADER_LEN);

    printf("[r.c] Header received.\n");
    memcpy(code, headBuff, CODE_LEN);

    if (uses_flags == true && strcmp(code, FAILURE_RSP) != 0)
    {
        memcpy(val, headBuff + CODE_LEN, HEADER_LEN - CODE_LEN);
    }
    else if(uses_flags == true)
    {
        memcpy(flags, headBuff + CODE_LEN, RESPONSE_LEN);
        memcpy(val, headBuff + CODE_LEN + RESPONSE_LEN, HEADER_LEN - CODE_LEN - RESPONSE_LEN);
    }
    else if (uses_flags == false)
    {
        memcpy(val, headBuff + CODE_LEN, HEADER_LEN - CODE_LEN);
    }
    else 
    {
        printf("[r.c] Error: Unknown header code.\n");
        return "-1";
    }

    char *ptr = strchr(val, ' ');
    *ptr = '\0';

    printf(" > Codes: %s\n", code);
    if (uses_flags == true){
        printf(" > Flags: %s\n", flags);
    }
    printf(" > Value: %s\n", val);


    // READING MESSAGE
    read(sockfd, recvBuff, atoi(val));
    printf("[r.c] Message received.\n");

    if (strcmp(code, FAILURE_RSP) == 0)
    {
        char *stderr;
        sprintf(stderr, "stderr:%s", recvBuff);
        return stderr;
    }
    else if (strcmp(code, SUCCEED_RSP) == 0)
    {
        if(strncmp(flags, "S", 1) == 0)
        {
            char *stdout;
            sprintf(stdout, "stdout:%s", recvBuff);
            return stdout;
        }
        else
        {
            printf("[r.c] Error: Handling of 'I' / 'F' not enabled.\n");
        }
    }
    else
    {
        printf("[r.c] Error: Unknown header code.\n");
        return "-1";
    }
    return "-1";
}
// -----------------------------------------------------------------------------
// SENDING FUNCTIONS
// -----------------------------------------------------------------------------

// Sends message header to the socket.
int send_header(SERVER server, char *code, char *val)
{
    int sockfd;
    if (val == NULL)
    {
        val = "";
    }

    if (strlen(code) + strlen(val) > HEADER_LEN)
    {
        printf("[r.c] Error: Values for header are too long.\n");
        return -1;
    }

    char header[HEADER_LEN];
    int pad_len = HEADER_LEN - strlen(code) - strlen(val);
    char padding[pad_len];

    int msg_len = strlen(val);

    char send_len[4];
    sprintf(send_len, "%d", msg_len);

    for (int i = 0; i < pad_len; i++){
        padding[i] = ' ';
    }

    strcat(header, code);
    strcat(header, send_len);
    strcat(header, val);

    printf("[r.c] Sending header.\n");
    sockfd = connect_server(server);

    if (send(sockfd, header, strlen(header), 0) < 0)
    {
        printf("\n[r.c] Error: Header Sending Failed \n");
        return -1;
    }
    if (send(sockfd, val, msg_len, 0) < 0)
    {
        printf("\n[r.c] Error: Message Sending Failed \n");
        return -1;
    }

    return sockfd;
}

// Writes string to socket.
char *send_message(SERVER server, char *code, char *message)
{
    int sockfd;

    sockfd = send_header(server, code, message);
    char* receive = receive_header(sockfd, false);

    return receive;
}

// -----------------------------------------------------------------------------
// PRINTERS
// -----------------------------------------------------------------------------

int get_num_actionsets()
{
    int num_actionsets = 0;
    for (int i = 0; i < MAX_COMMANDS; i++)
    {
        if (actionsets[i].num_actions > 0)
        {
            num_actionsets++;
        }
    }
    return num_actionsets;
}

int get_num_servers()
{
    int num_servers = 0;
    for (int i = 0; i < MAX_SERVERS; i++)
    {
        if (strcmp(servers[i].host, "") != 0)
        {
            num_servers++;
        }
    }
    return num_servers;
}

void print_actionsets()
{
    printf("[r.c] printing actionsets ");
    printf("(%i found)\n", get_num_actionsets());
    for (int i = 0; i < MAX_COMMANDS; i++)
    {
        if (actionsets[i].num_actions > 0)
        {
            printf("\tactionset%d\n", i+1);
            for (int j = 0; j < actionsets[i].num_actions; j++)
            {
                printf("\t\t%s %s\n", actionsets[i].commands[j].location, actionsets[i].commands[j].command);
                for (int k = 0; k < MAX_COMMANDS; k++)
                {
                    if (strcmp(actionsets[i].commands[j].requires[k], "") != 0)
                    {
                        printf("\t\t\trequires:'%s' \n", actionsets[i].commands[j].requires[k]);
                    }
                }
            }
        }
    }
}

void print_servers()
{
    printf("[r.c] printing servers ");
    printf("(%d found)\n", get_num_servers());
    for (int i = 0; i < MAX_SERVERS; i++)
    {
        if (strcmp(servers[i].host, "") != 0)
        {
            printf("\t(%d) %s:%d (%s)\n", i + 1, servers[i].host, servers[i].port, servers[i].full_host);
        }
    }
}


// -----------------------------------------------------------------------------
// COMMUNICATION MANAGEMENT
// -----------------------------------------------------------------------------

// Executes the command on a server where command needs executing.

int exec_command(COMMAND comm, bool local)
{
    int try_index = server_index_cost_array[0];
    SERVER executor = servers[try_index];

    for (int i = 0; i < numServers; i++)
    {
        if (executor.local == local)
        {
            printf("[r.c] Server selected: %s\n", executor.full_host);
            char *sendBuff = comm.command;
            int len = strlen(sendBuff);
            char send_len[len];
            int sockfd;

            sprintf(send_len, "%d", len);
            send_header(executor, EXECUTE_GET, send_len);
            send_message(executor, EXECUTE_GET, comm.command);
            receive_header(executor.sockfd, false);
            return 1;
        }
        else
        {
            try_index++;
            SERVER executor = servers[try_index];
        }
    }
    return -1;
}

// Given actionset, attempts to execute all commands in the set.
int manage_commands(ACTIONSET actionset)
{
    for (int i = 0; i < actionset.num_actions; i++)
    {
        COMMAND comm = actionset.commands[i];

        if (strcmp(comm.location, "remote") == 0)
        {
            printf("[r.c] Executing remote command:\n > %s\n", comm.command);
            exec_command(comm, false);
        }
        else if (strcmp(comm.location, "local") == 0)
        {
            printf("[r.c] Executing local command:\n > %s\n", comm.command);
            exec_command(comm, true);
        }
        else
        {
            printf("[r.c] Error: Unknown command location.");
            return -1;
        }
    }
    return EXIT_SUCCESS;
}

int manage_actionsets()
{
    for (int set_index = 0; set_index < MAX_ACTIONSETS; set_index++)
    {
        if (actionsets[set_index].num_actions > 0)
        {
            if (manage_commands(actionsets[set_index]) != EXIT_SUCCESS)
            {
                printf("[r.c] Error: Failed to execute actionset.\n");
                return EXIT_FAILURE;
            }
        }
    }
    return EXIT_SUCCESS;
}



// -----------------------------------------------------------------------------
// MAIN
// -----------------------------------------------------------------------------

int main(int argc, char *argv[])
{
    FILE *rake_fp;

    if (argc > 2)
    {
        printf("[r.c] using rakefile path specified\n");
        rake_fp = fopen(argv[1], "r");
    } 
    else
    {
        printf("[r.c] using default rakefile path\n");
        char cwd[256];
        if (getcwd(cwd, 256) == NULL)
            return EXIT_FAILURE;
        cwd[strlen(cwd) - strlen("rake-c")] = '\0';
        strcat(cwd, "Rakefile");
        printf("\t%s\n", cwd);
        rake_fp = fopen(cwd, "r");
    }

    if (rake_fp == NULL)
    {
        perror("fopen");
        return EXIT_FAILURE;
    }

    if (read_rakefile(rake_fp) != EXIT_SUCCESS)
        return EXIT_FAILURE;


    print_actionsets();
    print_servers();

    manage_actionsets();

    return EXIT_SUCCESS;
}