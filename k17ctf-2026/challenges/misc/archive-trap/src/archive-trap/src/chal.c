#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAX_INPUT 256

int blocked(const char *s)
{
    const char *bad[] = {
        ";", "|", "&", "`", "$",
        "(", ")", "<", ">",
        "\n", "\r",
        "flag",
        "sh", "bash",
        NULL};

    for (int i = 0; bad[i]; i++)
    {
        if (strstr(s, bad[i]))
        {
            return 1;
        }
    }

    return 0;
}

int main(void)
{
    while (1)
    {
        char input[MAX_INPUT];
        char command[1024];

        puts("=========[Archive Inspector]=========");
        printf("Enter archive pattern: ");
        fflush(stdout);
        if (!fgets(input, sizeof(input), stdin))
        {
            return 1;
        }
        input[strcspn(input, "\n")] = '\0';

        if (blocked(input))
        {
            puts("You don't have permission for that");
            return 1;
        }

        snprintf(
            command,
            sizeof(command),
            "/bin/sh ./filter.sh ./box -maxdepth 1 -name %s -print",
            input);

        puts("\nInspecting...");
        system(command);
    }
    return 0;
}