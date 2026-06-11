#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "lvgl.h"
#include "src/drivers/sdl/lv_sdl_keyboard.h"
#include "src/drivers/sdl/lv_sdl_mouse.h"
#include "src/drivers/sdl/lv_sdl_window.h"
#include "src/misc/cache/lv_image_cache.h"
#include "src/misc/lv_timer.h"
#include <SDL2/SDL.h>
#include <stdlib.h>

#define EP_HOST_UI_HOR_RES 800
#define EP_HOST_UI_VER_RES 480
#define EP_HOST_UI_REFR_PERIOD_MS 16u
#define EP_HOST_UI_IMAGE_CACHE_SIZE (12u * 1024u * 1024u)
#define EP_HOST_UI_IMAGE_HEADER_CACHE_COUNT 64u

static int g_host_ui_port_initialized;
static int g_host_ui_port_should_quit;
static lv_display_t *g_host_ui_display;

static int ep_host_ui_port_event_watch(void *userdata, SDL_Event *event)
{
    (void)userdata;

    if (event == 0) {
        return 1;
    }

    if (event->type == SDL_QUIT ||
        (event->type == SDL_WINDOWEVENT && event->window.event == SDL_WINDOWEVENT_CLOSE)) {
        g_host_ui_port_should_quit = 1;
        exit(0);
    }

    return 1;
}

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
    SDL_AddEventWatch(ep_host_ui_port_event_watch, 0);

    g_host_ui_port_should_quit = 0;
    g_host_ui_port_initialized = 1;
    return EP_OK;
}

int ep_host_ui_port_deinit(void)
{
    if (g_host_ui_port_initialized) {
        SDL_DelEventWatch(ep_host_ui_port_event_watch, 0);
    }

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

    while (SDL_PollEvent(&event)) {
        if (event.type == SDL_QUIT ||
            (event.type == SDL_WINDOWEVENT && event.window.event == SDL_WINDOWEVENT_CLOSE)) {
            g_host_ui_port_should_quit = 1;
            exit(0);
            continue;
        }

        (void)SDL_PushEvent(&event);
        break;
    }

    return g_host_ui_port_should_quit;
}
