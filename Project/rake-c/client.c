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
    char location[MAX_NAME_LEN];    // remote/local
    char command[MAX_NAME_LEN];     // command to execute
    char requires[MAX_COMMANDS][MAX_NAME_LEN];    // files needed for execution
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
            }
        }
        else if (strncmp(linebuf, "actionset", strlen("actionset")) == 0)
        {
            actionset_index++;
            command_index = -1;
            requires_index = -1;
        }
        // finds requirements of lines
        else if (linebuf[0] == '\t' && linebuf[1] == '\t')
        {
            // split line on space and store in array
            char *token = strtok(linebuf + 2 + strlen("requires"), " ");

            while (token != NULL)
            {
                requires_index++;
                strcpy(actionsets[actionset_index].commands[command_index].requires[requires_index], token);
                token = strtok(NULL, " ");
            }
        }
        // finds commands in rakefile
        else if (linebuf[0] == '\t')
        {
            command_index++;
            actionsets[actionset_index].num_actions++;

            // determines whether line is remote or locally executed
            if (strncmp(linebuf, "\tremote-", 8) == 0)
            {
                strcpy(actionsets[actionset_index].commands[command_index].location, "remote");
                strcpy(actionsets[actionset_index].commands[command_index].command, linebuf + 8);
            }
            else
            {
                strcpy(actionsets[actionset_index].commands[command_index].location, "local");
                strcpy(actionsets[actionset_index].commands[command_index].command, linebuf + 1);
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


// -----------------------------------------------------------------------------
// COMMUNICATION MANAGEMENT
// -----------------------------------------------------------------------------

// Manages the approach to take by the servers header received.
int manage_response(HEADER receive){
    if (receive.code == EXECUTE_GET)
    {
        // handle  execcost response
    }
    else if (receive.code == SUCCEED_RSP)
    {
        // handle  success response
    }
    else if (receive.code == FAILURE_RSP)
    {
        // handle  failure response
    }
    else if (receive.code == FILENAME)
    {
        // handle  filename response
    }
    else if (receive.code == FILESIZE)
    {
        // handle  filesize response
    }
    else if (receive.code == FILETRAN)
    {
        // handle  filetran response
    }
}


// -----------------------------------------------------------------------------
// SENDING FUNCTIONS
// -----------------------------------------------------------------------------

// Sends message header to the socket.
int send_header(int sockfd, char *code, char* val){
    if (val == NULL) {
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
    memset(padding, ' ', pad_len);
    sprintf(header, "%s%s%s", code, val, padding);

    printf("[r.c] Sending header.\n");
    if (send(sockfd, header, strlen(header), 0) < 0)
    {
        printf("\n[r.c] Error: Send Failed \n");
        return -1;
    }
    return 1;
}

// Writes string to socket.
int send_message(int sockfd, char *code, char *message)
{
    char len = strlen(message);
    char *len_str;
    sprintf(len_str, "%d", len);

    send_header(sockfd, code, len_str);
    HEADER receive = receive_header(sockfd, false);
}

// -----------------------------------------------------------------------------
// RECEIVING FUNCTIONS
// -----------------------------------------------------------------------------

// Sends message header to the socket.
HEADER receive_header(int sockfd, bool uses_flags)
{
    HEADER header = {
        .code = NULL,
        .flags = NULL,
        .length = NULL
    };

    if (sockfd < 0)
    {
        printf("[r.c] Error: Socket is not open.\n");
        return header;
    }
    char *code;
    char *len;
    char *flags = NULL;
    char *recvBuff;

    recvBuff = read(sockfd, recvBuff, HEADER_LEN);
    if (recvBuff == NULL)
    {
        printf("[r.c] Error: Could not read from socket.\n");
        return header;
    }

    printf("[r.c] Header received.\n");
    memcpy(code, recvBuff, CODE_LEN);

    if (uses_flags == true)
    {
        memcpy(flags, recvBuff + CODE_LEN, HEADER_LEN - CODE_LEN);
        memcpy(len, recvBuff + CODE_LEN + RESPONSE_LEN, HEADER_LEN - CODE_LEN - RESPONSE_LEN);
    }
    else 
    {
        memcpy(len, recvBuff + CODE_LEN, HEADER_LEN - CODE_LEN);
    }

    char *ptr = strchr(len, " ");
    *ptr = '\0';

    printf(" > Code: %s\n", code);
    printf(" > Flag: %s\n", code);
    printf(" > Leng: %s\n", len);

    HEADER header = {
        .code = code,
        .flags = flags,
        .length = len,
    };

    return header;
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

    

    return EXIT_SUCCESS;
}