#pragma once

#include <stdio.h>

FILE *host_tracked_fopen(const char *path, const char *mode);
int host_tracked_fclose(FILE *file);
size_t host_tracked_fread(void *buffer, size_t size, size_t count, FILE *file);
int host_open_file_count(void);
void host_fail_fread_after(int successful_calls);
void host_clear_fread_failure(void);
