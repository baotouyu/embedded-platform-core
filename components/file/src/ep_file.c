#include "ep_file.h"
#include "ep_osal_err.h"

int ep_file_open(ep_file_t **file, const char *path, int mode)
{
    (void)file;
    (void)path;
    (void)mode;
    return EP_ERR_UNSUPPORTED;
}

int ep_file_read(ep_file_t *file, void *buffer, size_t buffer_size, size_t *bytes_read)
{
    (void)file;
    (void)buffer;
    (void)buffer_size;
    if (bytes_read != 0) {
        *bytes_read = 0u;
    }
    return EP_ERR_UNSUPPORTED;
}

int ep_file_write(ep_file_t *file, const void *buffer, size_t buffer_size, size_t *bytes_written)
{
    (void)file;
    (void)buffer;
    (void)buffer_size;
    if (bytes_written != 0) {
        *bytes_written = 0u;
    }
    return EP_ERR_UNSUPPORTED;
}

int ep_file_close(ep_file_t *file)
{
    (void)file;
    return EP_ERR_UNSUPPORTED;
}
