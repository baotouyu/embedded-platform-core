#include "sqlite3.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    sqlite3_file base;
    FILE *file;
} ep_rtos_sqlite_file_t;

static int ep_rtos_sqlite_current_time_int64(sqlite3_vfs *vfs, sqlite3_int64 *time_out);

static int ep_rtos_sqlite_close(sqlite3_file *file)
{
    ep_rtos_sqlite_file_t *rtos_file = (ep_rtos_sqlite_file_t *)file;

    if (rtos_file->file != NULL) {
        (void)fclose(rtos_file->file);
        rtos_file->file = NULL;
    }

    return SQLITE_OK;
}

static int ep_rtos_sqlite_read(
    sqlite3_file *file,
    void *buffer,
    int amount,
    sqlite3_int64 offset)
{
    ep_rtos_sqlite_file_t *rtos_file = (ep_rtos_sqlite_file_t *)file;
    size_t read_size;

    if (rtos_file->file == NULL || buffer == NULL || amount < 0 || offset < 0) {
        return SQLITE_IOERR_READ;
    }

    if (fseek(rtos_file->file, (long)offset, SEEK_SET) != 0) {
        return SQLITE_IOERR_SEEK;
    }

    read_size = fread(buffer, 1u, (size_t)amount, rtos_file->file);
    if (read_size == (size_t)amount) {
        return SQLITE_OK;
    }

    if (read_size < (size_t)amount) {
        (void)memset((unsigned char *)buffer + read_size, 0, (size_t)amount - read_size);
    }

    return SQLITE_IOERR_SHORT_READ;
}

static int ep_rtos_sqlite_write(
    sqlite3_file *file,
    const void *buffer,
    int amount,
    sqlite3_int64 offset)
{
    (void)file;
    (void)buffer;
    (void)amount;
    (void)offset;
    return SQLITE_READONLY;
}

static int ep_rtos_sqlite_truncate(sqlite3_file *file, sqlite3_int64 size)
{
    (void)file;
    (void)size;
    return SQLITE_READONLY;
}

static int ep_rtos_sqlite_sync(sqlite3_file *file, int flags)
{
    (void)file;
    (void)flags;
    return SQLITE_OK;
}

static int ep_rtos_sqlite_file_size(sqlite3_file *file, sqlite3_int64 *size)
{
    ep_rtos_sqlite_file_t *rtos_file = (ep_rtos_sqlite_file_t *)file;
    long current;
    long end;

    if (rtos_file->file == NULL || size == NULL) {
        return SQLITE_IOERR_FSTAT;
    }

    current = ftell(rtos_file->file);
    if (current < 0) {
        return SQLITE_IOERR_FSTAT;
    }

    if (fseek(rtos_file->file, 0, SEEK_END) != 0) {
        return SQLITE_IOERR_FSTAT;
    }

    end = ftell(rtos_file->file);
    if (end < 0) {
        return SQLITE_IOERR_FSTAT;
    }

    if (fseek(rtos_file->file, current, SEEK_SET) != 0) {
        return SQLITE_IOERR_SEEK;
    }

    *size = (sqlite3_int64)end;
    return SQLITE_OK;
}

static int ep_rtos_sqlite_lock(sqlite3_file *file, int lock_type)
{
    (void)file;
    (void)lock_type;
    return SQLITE_OK;
}

static int ep_rtos_sqlite_unlock(sqlite3_file *file, int lock_type)
{
    (void)file;
    (void)lock_type;
    return SQLITE_OK;
}

static int ep_rtos_sqlite_check_reserved_lock(sqlite3_file *file, int *reserved)
{
    (void)file;

    if (reserved != NULL) {
        *reserved = 0;
    }

    return SQLITE_OK;
}

static int ep_rtos_sqlite_file_control(sqlite3_file *file, int op, void *arg)
{
    (void)file;
    (void)op;
    (void)arg;
    return SQLITE_NOTFOUND;
}

static int ep_rtos_sqlite_sector_size(sqlite3_file *file)
{
    (void)file;
    return 512;
}

static int ep_rtos_sqlite_device_characteristics(sqlite3_file *file)
{
    (void)file;
    return SQLITE_IOCAP_IMMUTABLE;
}

static const sqlite3_io_methods ep_rtos_sqlite_io_methods = {
    1,
    ep_rtos_sqlite_close,
    ep_rtos_sqlite_read,
    ep_rtos_sqlite_write,
    ep_rtos_sqlite_truncate,
    ep_rtos_sqlite_sync,
    ep_rtos_sqlite_file_size,
    ep_rtos_sqlite_lock,
    ep_rtos_sqlite_unlock,
    ep_rtos_sqlite_check_reserved_lock,
    ep_rtos_sqlite_file_control,
    ep_rtos_sqlite_sector_size,
    ep_rtos_sqlite_device_characteristics,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
};

static int ep_rtos_sqlite_open(
    sqlite3_vfs *vfs,
    sqlite3_filename name,
    sqlite3_file *file,
    int flags,
    int *out_flags)
{
    ep_rtos_sqlite_file_t *rtos_file = (ep_rtos_sqlite_file_t *)file;

    (void)vfs;
    (void)flags;

    if (name == NULL) {
        return SQLITE_IOERR;
    }

    (void)memset(rtos_file, 0, sizeof(*rtos_file));
    rtos_file->file = fopen(name, "rb");
    if (rtos_file->file == NULL) {
        return SQLITE_CANTOPEN;
    }

    rtos_file->base.pMethods = &ep_rtos_sqlite_io_methods;
    if (out_flags != NULL) {
        *out_flags = SQLITE_OPEN_READONLY;
    }

    return SQLITE_OK;
}

static int ep_rtos_sqlite_delete(sqlite3_vfs *vfs, const char *name, int sync_dir)
{
    (void)vfs;
    (void)name;
    (void)sync_dir;
    return SQLITE_READONLY;
}

static int ep_rtos_sqlite_access(
    sqlite3_vfs *vfs,
    const char *name,
    int flags,
    int *result)
{
    FILE *file;

    (void)vfs;
    (void)flags;

    if (result == NULL) {
        return SQLITE_IOERR;
    }

    file = fopen(name, "rb");
    if (file == NULL) {
        *result = 0;
        return SQLITE_OK;
    }

    (void)fclose(file);
    *result = 1;
    return SQLITE_OK;
}

static int ep_rtos_sqlite_full_pathname(
    sqlite3_vfs *vfs,
    const char *name,
    int out_size,
    char *out)
{
    size_t name_len;

    (void)vfs;

    if (name == NULL || out == NULL || out_size <= 0) {
        return SQLITE_IOERR;
    }

    name_len = strlen(name);
    if (name_len + 1u > (size_t)out_size) {
        return SQLITE_CANTOPEN_FULLPATH;
    }

    (void)memcpy(out, name, name_len + 1u);
    return SQLITE_OK;
}

static void *ep_rtos_sqlite_dl_open(sqlite3_vfs *vfs, const char *filename)
{
    (void)vfs;
    (void)filename;
    return NULL;
}

static void ep_rtos_sqlite_dl_error(sqlite3_vfs *vfs, int out_size, char *out)
{
    (void)vfs;
    if (out != NULL && out_size > 0) {
        out[0] = '\0';
    }
}

static void (*ep_rtos_sqlite_dl_sym(sqlite3_vfs *vfs, void *handle, const char *symbol))(void)
{
    (void)vfs;
    (void)handle;
    (void)symbol;
    return NULL;
}

static void ep_rtos_sqlite_dl_close(sqlite3_vfs *vfs, void *handle)
{
    (void)vfs;
    (void)handle;
}

static int ep_rtos_sqlite_randomness(sqlite3_vfs *vfs, int out_size, char *out)
{
    (void)vfs;
    if (out != NULL && out_size > 0) {
        (void)memset(out, 0, (size_t)out_size);
    }
    return out_size;
}

static int ep_rtos_sqlite_sleep(sqlite3_vfs *vfs, int microseconds)
{
    (void)vfs;
    return microseconds;
}

static int ep_rtos_sqlite_current_time(sqlite3_vfs *vfs, double *time_out)
{
    sqlite3_int64 now;

    if (time_out == NULL) {
        return SQLITE_IOERR;
    }

    if (ep_rtos_sqlite_current_time_int64(vfs, &now) != SQLITE_OK) {
        return SQLITE_IOERR;
    }

    *time_out = (double)now / 86400000.0;
    return SQLITE_OK;
}

static int ep_rtos_sqlite_get_last_error(sqlite3_vfs *vfs, int out_size, char *out)
{
    (void)vfs;
    if (out != NULL && out_size > 0) {
        out[0] = '\0';
    }
    return 0;
}

static int ep_rtos_sqlite_current_time_int64(sqlite3_vfs *vfs, sqlite3_int64 *time_out)
{
    time_t now;

    (void)vfs;

    if (time_out == NULL) {
        return SQLITE_IOERR;
    }

    now = time(NULL);
    *time_out = ((sqlite3_int64)now * 1000) + 210866760000000LL;
    return SQLITE_OK;
}

static sqlite3_vfs ep_rtos_sqlite_vfs = {
    2,
    sizeof(ep_rtos_sqlite_file_t),
    256,
    NULL,
    "ep_rtos",
    NULL,
    ep_rtos_sqlite_open,
    ep_rtos_sqlite_delete,
    ep_rtos_sqlite_access,
    ep_rtos_sqlite_full_pathname,
    ep_rtos_sqlite_dl_open,
    ep_rtos_sqlite_dl_error,
    ep_rtos_sqlite_dl_sym,
    ep_rtos_sqlite_dl_close,
    ep_rtos_sqlite_randomness,
    ep_rtos_sqlite_sleep,
    ep_rtos_sqlite_current_time,
    ep_rtos_sqlite_get_last_error,
    ep_rtos_sqlite_current_time_int64,
    NULL,
    NULL,
    NULL,
};

int sqlite3_os_init(void)
{
    return sqlite3_vfs_register(&ep_rtos_sqlite_vfs, 1);
}

int sqlite3_os_end(void)
{
    return SQLITE_OK;
}
