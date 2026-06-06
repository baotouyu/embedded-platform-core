#include "app_selftest.h"

#include "app_events.h"
#include "ep_event.h"
#include "ep_log.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"
#include "ep_timer.h"

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

int app_selftest_run(app_context_t *app)
{
    unsigned int waited_ms = 0u;
    int rc;

    if (app == 0) {
        return EP_ERR_INVAL;
    }

    g_app_timer_done = 0;

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

    return EP_OK;
}
