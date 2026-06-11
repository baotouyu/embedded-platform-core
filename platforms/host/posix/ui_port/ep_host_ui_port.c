#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "lvgl.h"
#include "src/drivers/sdl/lv_sdl_keyboard.h"
#include "src/drivers/sdl/lv_sdl_mouse.h"
#include "src/drivers/sdl/lv_sdl_window.h"
#include "src/misc/cache/lv_image_cache.h"
#include "src/misc/lv_timer.h"
#include <SDL2/SDL.h>

#define EP_HOST_UI_HOR_RES 800
#define EP_HOST_UI_VER_RES 480
#define EP_HOST_UI_REFR_PERIOD_MS 16u
#define EP_HOST_UI_IMAGE_CACHE_SIZE (12u * 1024u * 1024u)
#define EP_HOST_UI_IMAGE_HEADER_CACHE_COUNT 64u

static int g_host_ui_port_initialized;
static int g_host_ui_port_should_quit;
static lv_display_t *g_host_ui_display;

int ep_host_ui_port_init(void)
{
    if (g_host_ui_port_initialized) {
        return EP_OK;
    }

    g_host_ui_display = lv_sdl_window_create(EP_HOST_UI_HOR_RES, EP_HOST_UI_VER_RES);
    if (g_host_ui_display == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_image_cache_resize(EP_HOST_UI_IMAGE_CACHE_SIZE, true);
    lv_image_header_cache_resize(EP_HOST_UI_IMAGE_HEADER_CACHE_COUNT, true);
    lv_timer_t *refresh_timer = lv_display_get_refr_timer(g_host_ui_display);
    if (refresh_timer != 0) {
        lv_timer_set_period(refresh_timer, EP_HOST_UI_REFR_PERIOD_MS);
    }

    lv_sdl_window_set_title(g_host_ui_display, "embedded-platform-core host SDL2");
    lv_sdl_mouse_create();
    lv_sdl_keyboard_create();

    g_host_ui_port_should_quit = 0;
    g_host_ui_port_initialized = 1;
    return EP_OK;
}

int ep_host_ui_port_deinit(void)
{
    g_host_ui_display = 0;
    g_host_ui_port_initialized = 0;
    g_host_ui_port_should_quit = 1;
    return EP_OK;
}

int ep_host_ui_port_should_quit(void)
{
    SDL_Event event;

    if (!g_host_ui_port_initialized) {
        return 1;
    }

    if (SDL_PeepEvents(&event, 1, SDL_PEEKEVENT, SDL_QUIT, SDL_QUIT) > 0) {
        g_host_ui_port_should_quit = 1;
    }

    return g_host_ui_port_should_quit;
}
