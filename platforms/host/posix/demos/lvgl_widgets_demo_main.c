#include "demos/widgets/lv_demo_widgets.h"
#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"
#include "ep_ui.h"

#define EP_HOST_LVGL_WIDGETS_DEMO_FRAME_DELAY_MS 16u

int main(void)
{
    int rc = ep_ui_init();
    uint64_t frame_elapsed_ms;
    uint64_t frame_start_ms;
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_host_ui_port_init();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    lv_demo_widgets();

    while (!ep_host_ui_port_should_quit()) {
        frame_start_ms = ep_time_now_ms();

        rc = ep_ui_tick_inc(EP_HOST_LVGL_WIDGETS_DEMO_FRAME_DELAY_MS);
        if (rc != EP_OK) {
            (void)ep_host_ui_port_deinit();
            (void)ep_ui_deinit();
            return rc;
        }

        rc = ep_ui_process();
        if (rc != EP_OK) {
            (void)ep_host_ui_port_deinit();
            (void)ep_ui_deinit();
            return rc;
        }

        frame_elapsed_ms = ep_time_now_ms() - frame_start_ms;
        if (frame_elapsed_ms < EP_HOST_LVGL_WIDGETS_DEMO_FRAME_DELAY_MS) {
            ep_sleep_ms((unsigned int)(EP_HOST_LVGL_WIDGETS_DEMO_FRAME_DELAY_MS - frame_elapsed_ms));
        }
    }

    rc = ep_host_ui_port_deinit();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    return ep_ui_deinit();
}
