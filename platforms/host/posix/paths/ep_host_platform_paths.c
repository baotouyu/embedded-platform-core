#include "ep_platform_paths.h"

#include "ep_osal_err.h"

#include <stddef.h>
#include <string.h>

#define EP_HOST_CONFIG_PROFILE_PATH "config/profiles/host.cfg"
#define EP_HOST_RESOURCE_ROOT_PATH "resources/host"
#define EP_HOST_LVGL_FS_PREFIX "A:"

static int ep_host_is_valid_relative_path(const char *path)
{
    const char *cursor;

    if (path == NULL || path[0] == '\0') {
        return 0;
    }

    if (path[0] == '/') {
        return 0;
    }

    cursor = path;
    while (*cursor != '\0') {
        if (cursor[0] == '.' &&
            cursor[1] == '.' &&
            (cursor == path || cursor[-1] == '/') &&
            (cursor[2] == '\0' || cursor[2] == '/')) {
            return 0;
        }

        cursor++;
    }

    return 1;
}

static int ep_host_join_path(
    const char *base,
    const char *relative_path,
    char *buffer,
    size_t buffer_size)
{
    size_t base_len;
    size_t relative_len;
    size_t required_size;

    if (!ep_host_is_valid_relative_path(relative_path) || buffer == NULL || buffer_size == 0u) {
        return EP_ERR_INVAL;
    }

    base_len = strlen(base);
    relative_len = strlen(relative_path);
    required_size = base_len + 1u + relative_len + 1u;

    if (required_size > buffer_size) {
        buffer[0] = '\0';
        return EP_ERR_INVAL;
    }

    (void)memcpy(buffer, base, base_len);
    buffer[base_len] = '/';
    (void)memcpy(&buffer[base_len + 1u], relative_path, relative_len + 1u);

    return EP_OK;
}

static int ep_host_resource_category_path(
    const char *category,
    const char *name,
    char *buffer,
    size_t buffer_size)
{
    char relative_path[128];
    size_t category_len;
    size_t name_len;
    size_t required_size;

    if (!ep_host_is_valid_relative_path(name)) {
        return EP_ERR_INVAL;
    }

    category_len = strlen(category);
    name_len = strlen(name);
    required_size = category_len + 1u + name_len + 1u;

    if (required_size > sizeof(relative_path)) {
        return EP_ERR_INVAL;
    }

    (void)memcpy(relative_path, category, category_len);
    relative_path[category_len] = '/';
    (void)memcpy(&relative_path[category_len + 1u], name, name_len + 1u);

    return ep_host_join_path(EP_HOST_RESOURCE_ROOT_PATH, relative_path, buffer, buffer_size);
}

const char *ep_platform_config_profile_path(void)
{
    return EP_HOST_CONFIG_PROFILE_PATH;
}

const char *ep_platform_resource_root_path(void)
{
    return EP_HOST_RESOURCE_ROOT_PATH;
}

int ep_platform_asset_path(const char *relative_path, char *buffer, size_t buffer_size)
{
    return ep_host_join_path(EP_HOST_RESOURCE_ROOT_PATH, relative_path, buffer, buffer_size);
}

int ep_platform_image_path(const char *name, char *buffer, size_t buffer_size)
{
    return ep_host_resource_category_path("images", name, buffer, buffer_size);
}

int ep_platform_lvgl_image_src(const char *name, char *buffer, size_t buffer_size)
{
    char image_path[160];
    size_t prefix_len;
    size_t path_len;
    size_t required_size;
    int rc;

    if (buffer == NULL || buffer_size == 0u) {
        return EP_ERR_INVAL;
    }

    rc = ep_platform_image_path(name, image_path, sizeof(image_path));
    if (rc != EP_OK) {
        buffer[0] = '\0';
        return rc;
    }

    prefix_len = strlen(EP_HOST_LVGL_FS_PREFIX);
    path_len = strlen(image_path);
    required_size = prefix_len + path_len + 1u;
    if (required_size > buffer_size) {
        buffer[0] = '\0';
        return EP_ERR_INVAL;
    }

    (void)memcpy(buffer, EP_HOST_LVGL_FS_PREFIX, prefix_len);
    (void)memcpy(&buffer[prefix_len], image_path, path_len + 1u);

    return EP_OK;
}

int ep_platform_recipe_path(const char *name, char *buffer, size_t buffer_size)
{
    return ep_host_resource_category_path("recipe", name, buffer, buffer_size);
}

int ep_platform_lvgl_recipe_src(const char *name, char *buffer, size_t buffer_size)
{
    char recipe_path[160];
    size_t prefix_len;
    size_t path_len;
    size_t required_size;
    int rc;

    if (buffer == NULL || buffer_size == 0u) {
        return EP_ERR_INVAL;
    }

    rc = ep_platform_recipe_path(name, recipe_path, sizeof(recipe_path));
    if (rc != EP_OK) {
        buffer[0] = '\0';
        return rc;
    }

    prefix_len = strlen(EP_HOST_LVGL_FS_PREFIX);
    path_len = strlen(recipe_path);
    required_size = prefix_len + path_len + 1u;
    if (required_size > buffer_size) {
        buffer[0] = '\0';
        return EP_ERR_INVAL;
    }

    (void)memcpy(buffer, EP_HOST_LVGL_FS_PREFIX, prefix_len);
    (void)memcpy(&buffer[prefix_len], recipe_path, path_len + 1u);

    return EP_OK;
}

int ep_platform_font_path(const char *name, char *buffer, size_t buffer_size)
{
    return ep_host_resource_category_path("fonts", name, buffer, buffer_size);
}

int ep_platform_theme_path(const char *name, char *buffer, size_t buffer_size)
{
    return ep_host_resource_category_path("themes", name, buffer, buffer_size);
}
