#ifndef EP_EVENT_H
#define EP_EVENT_H

#include <stddef.h>

typedef int ep_event_id_t;

typedef void (*ep_event_handler_t)(
    ep_event_id_t event_id,
    const void *payload,
    size_t payload_size,
    void *user_data
);

int ep_event_init(void);
int ep_event_subscribe(ep_event_id_t event_id, ep_event_handler_t handler, void *user_data);
int ep_event_publish(ep_event_id_t event_id, const void *payload, size_t payload_size, unsigned int timeout_ms);

#endif
