#include "ep_timer.h"
#include "ep_event.h"
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_thread.h"
#include "ep_osal_time.h"

#include <stddef.h>
#include <stdint.h>

#define EP_TIMER_MAX_TIMERS 16u
#define EP_TIMER_SCAN_PERIOD_MS 10u

struct ep_timer_entry {
    int active;
    ep_timer_id_t timer_id;
    ep_event_id_t event_id;
    uint64_t deadline_ms;
};

static ep_thread_t *g_timer_thread;
static ep_mutex_t *g_timer_lock;
static struct ep_timer_entry g_timers[EP_TIMER_MAX_TIMERS];
static int g_timer_started;

static void *ep_timer_scan_loop(void *arg)
{
    (void)arg;

    for (;;) {
        ep_sleep_ms(EP_TIMER_SCAN_PERIOD_MS);
    }

    return 0;
}

int ep_timer_init(void)
{
    int rc;

    if (g_timer_started) {
        return EP_OK;
    }

    rc = ep_event_init();
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_mutex_create(&g_timer_lock);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_thread_create(&g_timer_thread, "timer", ep_timer_scan_loop, 0);
    if (rc != EP_OK) {
        return rc;
    }

    g_timer_started = 1;
    return EP_OK;
}

int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id)
{
    (void)timeout_ms;
    (void)event_id;

    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_timer_stop(ep_timer_id_t timer_id)
{
    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_INVAL;
}
