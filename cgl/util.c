#include "util.h"

#include <stdio.h>
#include <stdlib.h>

char *read_file(const char *filename) {
    char *buffer = 0;
    long length;
    FILE *f = fopen(filename, "rb");

    if (f) {
        fseek(f, 0, SEEK_END);
        length = ftell(f);
        fseek(f, 0, SEEK_SET);
        buffer = malloc(length);
        if (buffer) {
            fread(buffer, 1, length, f);
        }
        fclose(f);
    }
    return buffer;
}

void free_file_data(char *filedata) { free(filedata); }