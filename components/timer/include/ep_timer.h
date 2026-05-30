#ifndef EP_TIMER_H
#define EP_TIMER_H

#include "ep_event.h"

typedef int ep_timer_id_t;

int ep_timer_init(void);
int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id);
int ep_timer_stop(ep_timer_id_t timer_id);

#endif
