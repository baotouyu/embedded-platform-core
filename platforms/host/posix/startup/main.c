#include "ep_framework.h"

#if defined(EP_HAS_HOST_SDL2_UI)
#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"
#include "ep_ui.h"
#include "lvgl.h"

#define EP_HOST_UI_FRAME_COUNT 30u
#define EP_HOST_UI_FRAME_DELAY_MS 16u
#endif

int ep_platform_boot(void)
{
    return 0;
}

#if defined(EP_HAS_HOST_SDL2_UI)
static int ep_host_run_sdl2_ui_demo(void)
{
    unsigned int frame;
    int rc = ep_ui_init();
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_host_ui_port_init();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    lv_obj_t *label = lv_label_create(lv_screen_active());
    if (label == 0) {
        (void)ep_host_ui_port_deinit();
        (void)ep_ui_deinit();
        return EP_ERR_UNSUPPORTED;
    }

    lv_label_set_text(label, "embedded-platform-core host SDL2");
    lv_obj_center(label);

    for (frame = 0u; frame < EP_HOST_UI_FRAME_COUNT; frame++) {
        rc = ep_ui_process();
        if (rc != EP_OK) {
            (void)ep_host_ui_port_deinit();
            (void)ep_ui_deinit();
            return rc;
        }

        ep_sleep_ms(EP_HOST_UI_FRAME_DELAY_MS);
    }

    rc = ep_host_ui_port_deinit();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    return ep_ui_deinit();
}
#endif

int main(void)
{
    int rc = ep_framework_start();
    if (rc != 0) {
        return rc;
    }

#if defined(EP_HAS_HOST_SDL2_UI)
    return ep_host_run_sdl2_ui_demo();
#else
    return 0;
#endif
}
