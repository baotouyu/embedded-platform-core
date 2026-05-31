#include "ep_file.h"
#include "ep_osal_err.h"
#include "ep_platform_paths.h"

#include <stddef.h>

#define EP_HOST_RESOURCE_SMOKE_PATH_SIZE 128u
#define EP_HOST_RESOURCE_SMOKE_READ_SIZE 32u

typedef int (*ep_host_resource_path_fn_t)(const char *name, char *buffer, size_t buffer_size);

static int ep_host_resource_smoke_read_file(const char *path)
{
    ep_file_t *file = 0;
    char buffer[EP_HOST_RESOURCE_SMOKE_READ_SIZE];
    size_t bytes_read = 0u;
    int rc;

    rc = ep_file_open(&file, path, EP_FILE_MODE_READ);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_file_read(file, buffer, sizeof(buffer), &bytes_read);
    if (rc != EP_OK) {
        (void)ep_file_close(file);
        return rc;
    }

    rc = ep_file_close(file);
    if (rc != EP_OK) {
        return rc;
    }

    return (bytes_read > 0u) ? EP_OK : EP_ERR_UNSUPPORTED;
}

static int ep_host_resource_smoke_check(
    ep_host_resource_path_fn_t path_fn,
    const char *name)
{
    char path[EP_HOST_RESOURCE_SMOKE_PATH_SIZE];
    int rc = path_fn(name, path, sizeof(path));

    if (rc != EP_OK) {
        return rc;
    }

    return ep_host_resource_smoke_read_file(path);
}

int main(void)
{
    int rc = ep_host_resource_smoke_check(ep_platform_image_path, "smoke.txt");
    if (rc != EP_OK) {
        return 1;
    }

    rc = ep_host_resource_smoke_check(ep_platform_font_path, "smoke.txt");
    if (rc != EP_OK) {
        return 2;
    }

    rc = ep_host_resource_smoke_check(ep_platform_theme_path, "smoke.txt");
    if (rc != EP_OK) {
        return 3;
    }

    return 0;
}
