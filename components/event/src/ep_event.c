#include "ep_event.h"
#include "ep_osal_err.h"

int ep_event_init(void)
{
    return EP_ERR_UNSUPPORTED;
}

int ep_event_subscribe(ep_event_id_t event_id, ep_event_handler_t handler, void *user_data)
{
    (void)event_id;
    (void)handler;
    (void)user_data;

    return EP_ERR_UNSUPPORTED;
}

int ep_event_publish(ep_event_id_t event_id, const void *payload, size_t payload_size, unsigned int timeout_ms)
{
    (void)event_id;
    (void)payload;
    (void)payload_size;
    (void)timeout_ms;

    return EP_ERR_UNSUPPORTED;
}
