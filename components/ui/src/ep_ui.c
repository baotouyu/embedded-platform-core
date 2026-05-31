#include "ep_ui.h"
#include "ep_osal_err.h"
#include "lvgl.h"

static int g_ui_initialized;

int ep_ui_init(void)
{
    if (g_ui_initialized) {
        return EP_OK;
    }

    lv_init();
    g_ui_initialized = 1;
    return EP_OK;
}

int ep_ui_tick_inc(unsigned int elapsed_ms)
{
    if (!g_ui_initialized) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_tick_inc(elapsed_ms);
    return EP_OK;
}

int ep_ui_process(void)
{
    if (!g_ui_initialized) {
        return EP_ERR_UNSUPPORTED;
    }

    (void)lv_timer_handler();
    return EP_OK;
}

int ep_ui_deinit(void)
{
    if (!g_ui_initialized) {
        return EP_OK;
    }

    lv_deinit();
    g_ui_initialized = 0;
    return EP_OK;
}
