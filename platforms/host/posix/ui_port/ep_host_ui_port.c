#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "lvgl.h"
#include "src/drivers/sdl/lv_sdl_keyboard.h"
#include "src/drivers/sdl/lv_sdl_mouse.h"
#include "src/drivers/sdl/lv_sdl_window.h"

static int g_host_ui_port_initialized;
static lv_display_t *g_host_ui_display;

int ep_host_ui_port_init(void)
{
    if (g_host_ui_port_initialized) {
        return EP_OK;
    }

    g_host_ui_display = lv_sdl_window_create(480, 320);
    if (g_host_ui_display == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_sdl_window_set_title(g_host_ui_display, "embedded-platform-core host SDL2");
    lv_sdl_mouse_create();
    lv_sdl_keyboard_create();

    g_host_ui_port_initialized = 1;
    return EP_OK;
}

int ep_host_ui_port_deinit(void)
{
    g_host_ui_display = 0;
    g_host_ui_port_initialized = 0;
    return EP_OK;
}
