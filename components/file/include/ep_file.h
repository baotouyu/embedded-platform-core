#ifndef EP_FILE_H
#define EP_FILE_H

#include <stddef.h>

#define EP_FILE_MODE_READ (1 << 0)
#define EP_FILE_MODE_WRITE (1 << 1)
#define EP_FILE_MODE_CREATE (1 << 2)
#define EP_FILE_MODE_TRUNCATE (1 << 3)
#define EP_FILE_MODE_APPEND (1 << 4)

typedef struct ep_file ep_file_t;

int ep_file_open(ep_file_t **file, const char *path, int mode);
int ep_file_read(ep_file_t *file, void *buffer, size_t buffer_size, size_t *bytes_read);
int ep_file_write(ep_file_t *file, const void *buffer, size_t buffer_size, size_t *bytes_written);
int ep_file_close(ep_file_t *file);

#endif
