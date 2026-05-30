#include "ep_timer.h"
#include "ep_osal_err.h"

int ep_timer_init(void)
{
    return EP_ERR_UNSUPPORTED;
}

int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id)
{
    (void)timer_id;
    (void)timeout_ms;
    (void)event_id;

    return EP_ERR_UNSUPPORTED;
}

int ep_timer_stop(ep_timer_id_t timer_id)
{
    (void)timer_id;

    return EP_ERR_UNSUPPORTED;
}
