#include "ep_file.h"
#include "ep_osal_err.h"

#include <stdio.h>
#include <stdlib.h>

struct ep_file {
    FILE *handle;
};

static int ep_file_mode_has(int mode, int flag)
{
    return (mode & flag) != 0;
}

static const char *ep_file_mode_to_stdio(int mode)
{
    const int known_mode_mask = EP_FILE_MODE_READ |
                                EP_FILE_MODE_WRITE |
                                EP_FILE_MODE_CREATE |
                                EP_FILE_MODE_TRUNCATE |
                                EP_FILE_MODE_APPEND;
    int read = ep_file_mode_has(mode, EP_FILE_MODE_READ);
    int write = ep_file_mode_has(mode, EP_FILE_MODE_WRITE);
    int create = ep_file_mode_has(mode, EP_FILE_MODE_CREATE);
    int truncate = ep_file_mode_has(mode, EP_FILE_MODE_TRUNCATE);
    int append = ep_file_mode_has(mode, EP_FILE_MODE_APPEND);

    if (mode == 0) {
        return 0;
    }

    if ((mode & ~known_mode_mask) != 0) {
        return 0;
    }

    if (!read && !write) {
        return 0;
    }

    if (append && truncate) {
        return 0;
    }

    if (append && !write) {
        return 0;
    }

    if (create && !write) {
        return 0;
    }

    if (truncate && !write) {
        return 0;
    }

    if (read && write && create && truncate) {
        return "wb+";
    }

    if (read && write && create) {
        return "ab+";
    }

    if (read && write) {
        return "rb+";
    }

    if (read) {
        return "rb";
    }

    if (write && create && truncate) {
        return "wb";
    }

    if (write && create && append) {
        return "ab";
    }

    if (write && create) {
        return "ab+";
    }

    return 0;
}

int ep_file_open(ep_file_t **file, const char *path, int mode)
{
    const char *stdio_mode;
    ep_file_t *new_file;
    FILE *handle;

    if (file == 0 || path == 0 || path[0] == '\0') {
        return EP_ERR_INVAL;
    }

    *file = 0;

    stdio_mode = ep_file_mode_to_stdio(mode);
    if (stdio_mode == 0) {
        return EP_ERR_INVAL;
    }

    handle = fopen(path, stdio_mode);
    if (handle == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    new_file = (ep_file_t *)malloc(sizeof(*new_file));
    if (new_file == 0) {
        (void)fclose(handle);
        return EP_ERR_BUSY;
    }

    new_file->handle = handle;
    *file = new_file;
    return EP_OK;
}

int ep_file_read(ep_file_t *file, void *buffer, size_t buffer_size, size_t *bytes_read)
{
    size_t count;

    if (bytes_read != 0) {
        *bytes_read = 0u;
    }

    if (file == 0 || (buffer == 0 && buffer_size > 0u)) {
        return EP_ERR_INVAL;
    }

    if (buffer_size == 0u) {
        return EP_OK;
    }

    count = fread(buffer, 1u, buffer_size, file->handle);
    if (bytes_read != 0) {
        *bytes_read = count;
    }

    if (count < buffer_size && ferror(file->handle) != 0) {
        return EP_ERR_UNSUPPORTED;
    }

    return EP_OK;
}

int ep_file_write(ep_file_t *file, const void *buffer, size_t buffer_size, size_t *bytes_written)
{
    size_t count;

    if (bytes_written != 0) {
        *bytes_written = 0u;
    }

    if (file == 0 || (buffer == 0 && buffer_size > 0u)) {
        return EP_ERR_INVAL;
    }

    if (buffer_size == 0u) {
        return EP_OK;
    }

    count = fwrite(buffer, 1u, buffer_size, file->handle);
    if (bytes_written != 0) {
        *bytes_written = count;
    }

    if (count != buffer_size) {
        return EP_ERR_UNSUPPORTED;
    }

    return EP_OK;
}

int ep_file_close(ep_file_t *file)
{
    int rc;

    if (file == 0) {
        return EP_ERR_INVAL;
    }

    rc = fclose(file->handle);
    free(file);

    return (rc == 0) ? EP_OK : EP_ERR_UNSUPPORTED;
}
