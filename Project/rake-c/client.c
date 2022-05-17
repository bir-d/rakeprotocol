// Client program in C99
// Compiled with:
//	mycc='cc -std=c99 -Wall -Werror'
#include "client.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdbool.h>

// bool prefix(const char *pre, const char *str)
// {
//     return strncmp(pre, str, strlen(pre)) == 0;
// }

int default_rakefile()
{
    char path[1024];
    if (getcwd(path, sizeof(path)) == NULL)
    {
        perror("getcwd() error");
        return 1;
    }
    char *filename = "/Rakefile";
    char *ptr = strrchr(path, '/');
    *ptr = '\0';
    strcat(path, filename);
    printf("Opening Rakefile at: %s\n", path);

    FILE *fp = fopen(path, "r");

    if (fp == NULL)
    {
        printf("Error: could not open file %s", filename);
        return 1;
    }

    const unsigned MAX_LENGTH = 256;
    char buffer[MAX_LENGTH];

    int default_port; // default port number
    int actionset_num = 1;
    char *hosts;       // 22 is the maximum length of a hostname (192.168.0.0:65535)
    char *commands; // array of commands
    char *actionsets [MAX_LENGTH][MAX_LENGTH]; // array of actionsets

    while (fgets(buffer, MAX_LENGTH, fp) != NULL)
    {
        // if the line starts with a '#' character, ignore it
        if (buffer[0] == '#')
        {
            continue;
        }
        // else if it starts with a '\n' character, ignore it
        else if (buffer[0] == '\n')
        {
            continue;
        }
        // else if it starts with a tab character, print it
        else if (buffer[0] == 'a')
        {
            printf("%s", buffer);
        }

        // else if it starts with a '\r' character, ignore it
        else if (buffer[0] == '\r')
        {
            continue;
        }
    }


    
    // while (fgets(buffer, MAX_LENGTH, fp))
    //     printf("%s", buffer);

    // close the file
    fclose(fp);

    return 0;
}

int main() 
{
    default_rakefile();
    return 0;
}