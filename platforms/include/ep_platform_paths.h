#ifndef EP_PLATFORM_PATHS_H
#define EP_PLATFORM_PATHS_H

#include <stddef.h>

const char *ep_platform_config_profile_path(void);
const char *ep_platform_resource_root_path(void);

int ep_platform_asset_path(const char *relative_path, char *buffer, size_t buffer_size);
int ep_platform_image_path(const char *name, char *buffer, size_t buffer_size);
int ep_platform_lvgl_image_src(const char *name, char *buffer, size_t buffer_size);
int ep_platform_recipe_path(const char *name, char *buffer, size_t buffer_size);
int ep_platform_lvgl_recipe_src(const char *name, char *buffer, size_t buffer_size);
int ep_platform_font_path(const char *name, char *buffer, size_t buffer_size);
int ep_platform_theme_path(const char *name, char *buffer, size_t buffer_size);

#endif
