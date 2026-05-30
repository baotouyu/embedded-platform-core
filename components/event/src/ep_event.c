#include "ep_event.h"
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_queue.h"
#include "ep_osal_thread.h"

#include <string.h>

#define EP_EVENT_MAX_HANDLERS 16u
#define EP_EVENT_MAX_PAYLOAD_SIZE 64u
#define EP_EVENT_QUEUE_DEPTH 16u

struct ep_event_message {
    ep_event_id_t event_id;
    size_t payload_size;
    unsigned char payload[EP_EVENT_MAX_PAYLOAD_SIZE];
};

struct ep_event_subscription {
    int used;
    ep_event_id_t event_id;
    ep_event_handler_t handler;
    void *user_data;
};

static ep_queue_t *g_event_queue;
static ep_thread_t *g_event_thread;
static ep_mutex_t *g_event_lock;
static struct ep_event_subscription g_subscriptions[EP_EVENT_MAX_HANDLERS];
static int g_event_started;

static void *ep_event_dispatch_loop(void *arg)
{
    (void)arg;

    for (;;) {
        struct ep_event_message message;
        (void)ep_queue_recv(g_event_queue, &message, 1000u);
    }

    return 0;
}

int ep_event_init(void)
{
    int rc;

    if (g_event_started) {
        return EP_OK;
    }

    rc = ep_mutex_create(&g_event_lock);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_queue_create(&g_event_queue, sizeof(struct ep_event_message), EP_EVENT_QUEUE_DEPTH);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_thread_create(&g_event_thread, "event-bus", ep_event_dispatch_loop, 0);
    if (rc != EP_OK) {
        return rc;
    }

    g_event_started = 1;
    return EP_OK;
}

int ep_event_subscribe(ep_event_id_t event_id, ep_event_handler_t handler, void *user_data)
{
    size_t i;
    int rc;

    if (handler == 0) {
        return EP_ERR_INVAL;
    }

    if (!g_event_started) {
        return EP_ERR_UNSUPPORTED;
    }

    rc = ep_mutex_lock(g_event_lock);
    if (rc != EP_OK) {
        return rc;
    }

    for (i = 0u; i < EP_EVENT_MAX_HANDLERS; ++i) {
        if (!g_subscriptions[i].used) {
            g_subscriptions[i].used = 1;
            g_subscriptions[i].event_id = event_id;
            g_subscriptions[i].handler = handler;
            g_subscriptions[i].user_data = user_data;
            (void)ep_mutex_unlock(g_event_lock);
            return EP_OK;
        }
    }

    (void)ep_mutex_unlock(g_event_lock);
    return EP_ERR_BUSY;
}

int ep_event_publish(ep_event_id_t event_id, const void *payload, size_t payload_size, unsigned int timeout_ms)
{
    struct ep_event_message message;

    if (!g_event_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (payload_size > EP_EVENT_MAX_PAYLOAD_SIZE) {
        return EP_ERR_INVAL;
    }

    if (payload_size > 0u && payload == 0) {
        return EP_ERR_INVAL;
    }

    message.event_id = event_id;
    message.payload_size = payload_size;
    if (payload_size > 0u) {
        (void)memcpy(message.payload, payload, payload_size);
    }

    return ep_queue_send(g_event_queue, &message, timeout_ms);
}
