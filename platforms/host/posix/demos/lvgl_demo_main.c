#include "app_ui.h"
#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"
#include "ep_ui.h"
#include "lvgl.h"

#define EP_HOST_LVGL_DEMO_FRAME_DELAY_MS 16u
#define EP_HOST_LVGL_DEMO_EXIT_TEXT "Exit"

static int g_demo_should_exit;

static void ep_host_lvgl_demo_on_exit(lv_event_t *event)
{
    (void)event;
    g_demo_should_exit = 1;
}

static int ep_host_lvgl_demo_create_screen(void)
{
    lv_obj_t *screen;
    lv_obj_t *button;
    lv_obj_t *button_label = 0;
    int rc = app_ui_create();

    if (rc != EP_OK) {
        return rc;
    }

    screen = lv_screen_active();
    button = lv_button_create(screen);
    if ((screen == 0) || (button == 0)) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_obj_set_size(button, 96, 36);
    lv_obj_align(button, LV_ALIGN_CENTER, 0, 42);
    lv_obj_add_event_cb(button, ep_host_lvgl_demo_on_exit, LV_EVENT_CLICKED, 0);

    button_label = lv_label_create(button);
    if (button_label == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_label_set_text(button_label, EP_HOST_LVGL_DEMO_EXIT_TEXT);
    lv_obj_center(button_label);

    return EP_OK;
}

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

    rc = ep_host_lvgl_demo_create_screen();
    if (rc != EP_OK) {
        (void)ep_host_ui_port_deinit();
        (void)ep_ui_deinit();
        return rc;
    }

    while (!g_demo_should_exit && !ep_host_ui_port_should_quit()) {
        frame_start_ms = ep_time_now_ms();

        rc = ep_ui_tick_inc(EP_HOST_LVGL_DEMO_FRAME_DELAY_MS);
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
        if (frame_elapsed_ms < EP_HOST_LVGL_DEMO_FRAME_DELAY_MS) {
            ep_sleep_ms((unsigned int)(EP_HOST_LVGL_DEMO_FRAME_DELAY_MS - frame_elapsed_ms));
        }
    }

    rc = ep_host_ui_port_deinit();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    return ep_ui_deinit();
}
