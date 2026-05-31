#include "app_events.h"
#include "app_main.h"
#include "ep_event.h"
#include "ep_log.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"
#include "ep_timer.h"

#if defined(EP_HAS_HOST_SDL2_UI)
#include "ep_host_ui_port.h"
#include "ep_ui.h"
#include "lvgl.h"
#endif

#define APP_TIMER_ID_SELF_TEST 1
#define APP_TIMER_TIMEOUT_MS 50u
#define APP_WAIT_STEP_MS 10u
#define APP_WAIT_TIMEOUT_MS 500u

static volatile int g_app_timer_done;

static void app_timer_done_handler(
    ep_event_id_t event_id,
    const void *payload,
    size_t payload_size,
    void *user_data
)
{
    (void)payload;
    (void)payload_size;
    (void)user_data;

    if (event_id == APP_EVENT_TIMER_DONE) {
        g_app_timer_done = 1;
    }
}

#if defined(EP_HAS_HOST_SDL2_UI)
#define APP_HOST_UI_FRAME_COUNT 30u
#define APP_HOST_UI_FRAME_DELAY_MS 16u

static int app_run_host_sdl2_ui_demo(void)
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

    for (frame = 0u; frame < APP_HOST_UI_FRAME_COUNT; frame++) {
        rc = ep_ui_process();
        if (rc != EP_OK) {
            (void)ep_host_ui_port_deinit();
            (void)ep_ui_deinit();
            return rc;
        }

        ep_sleep_ms(APP_HOST_UI_FRAME_DELAY_MS);
    }

    rc = ep_host_ui_port_deinit();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    return ep_ui_deinit();
}
#endif

int app_main(void)
{
    unsigned int waited_ms = 0u;
    int rc;

    g_app_timer_done = 0;

    EP_LOGI("app", "app lifecycle start");

    rc = ep_event_subscribe(APP_EVENT_TIMER_DONE, app_timer_done_handler, 0);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_timer_start(APP_TIMER_ID_SELF_TEST, APP_TIMER_TIMEOUT_MS, APP_EVENT_TIMER_DONE);
    if (rc != EP_OK) {
        return rc;
    }

    while (!g_app_timer_done && waited_ms < APP_WAIT_TIMEOUT_MS) {
        ep_sleep_ms(APP_WAIT_STEP_MS);
        waited_ms += APP_WAIT_STEP_MS;
    }

    if (!g_app_timer_done) {
        EP_LOGE("app", "app lifecycle timeout");
        return EP_ERR_TIMEOUT;
    }

#if defined(EP_HAS_HOST_SDL2_UI)
    rc = app_run_host_sdl2_ui_demo();
    if (rc != EP_OK) {
        return rc;
    }
#endif

    EP_LOGI("app", "app lifecycle done");
    return 0;
}
