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

struct ep_timer_expired_event {
    ep_event_id_t event_id;
};

static ep_thread_t *g_timer_thread;
static ep_mutex_t *g_timer_lock;
static struct ep_timer_entry g_timers[EP_TIMER_MAX_TIMERS];
static int g_timer_started;

static void *ep_timer_scan_loop(void *arg)
{
    (void)arg;

    for (;;) {
        struct ep_timer_expired_event expired[EP_TIMER_MAX_TIMERS];
        size_t expired_count = 0u;
        uint64_t now_ms;
        size_t i;

        ep_sleep_ms(EP_TIMER_SCAN_PERIOD_MS);
        now_ms = ep_time_now_ms();

        if (ep_mutex_lock(g_timer_lock) != EP_OK) {
            continue;
        }

        for (i = 0u; i < EP_TIMER_MAX_TIMERS; ++i) {
            if (g_timers[i].active && g_timers[i].deadline_ms <= now_ms) {
                expired[expired_count].event_id = g_timers[i].event_id;
                expired_count += 1u;
                g_timers[i].active = 0;
            }
        }

        (void)ep_mutex_unlock(g_timer_lock);

        for (i = 0u; i < expired_count; ++i) {
            (void)ep_event_publish(expired[i].event_id, 0, 0, 0);
        }
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
    uint64_t deadline_ms;
    size_t first_free = EP_TIMER_MAX_TIMERS;
    size_t i;
    int rc;

    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    deadline_ms = ep_time_now_ms() + timeout_ms;

    rc = ep_mutex_lock(g_timer_lock);
    if (rc != EP_OK) {
        return rc;
    }

    for (i = 0u; i < EP_TIMER_MAX_TIMERS; ++i) {
        if (g_timers[i].active && g_timers[i].timer_id == timer_id) {
            g_timers[i].deadline_ms = deadline_ms;
            g_timers[i].event_id = event_id;
            (void)ep_mutex_unlock(g_timer_lock);
            return EP_OK;
        }

        if (!g_timers[i].active && first_free == EP_TIMER_MAX_TIMERS) {
            first_free = i;
        }
    }

    if (first_free == EP_TIMER_MAX_TIMERS) {
        (void)ep_mutex_unlock(g_timer_lock);
        return EP_ERR_BUSY;
    }

    g_timers[first_free].active = 1;
    g_timers[first_free].timer_id = timer_id;
    g_timers[first_free].event_id = event_id;
    g_timers[first_free].deadline_ms = deadline_ms;

    (void)ep_mutex_unlock(g_timer_lock);
    return EP_OK;
}

int ep_timer_stop(ep_timer_id_t timer_id)
{
    size_t i;
    int rc;

    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    rc = ep_mutex_lock(g_timer_lock);
    if (rc != EP_OK) {
        return rc;
    }

    for (i = 0u; i < EP_TIMER_MAX_TIMERS; ++i) {
        if (g_timers[i].active && g_timers[i].timer_id == timer_id) {
            g_timers[i].active = 0;
            (void)ep_mutex_unlock(g_timer_lock);
            return EP_OK;
        }
    }

    (void)ep_mutex_unlock(g_timer_lock);
    return EP_ERR_INVAL;
}
