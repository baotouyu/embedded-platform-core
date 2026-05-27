#ifndef EP_OSAL_QUEUE_H
#define EP_OSAL_QUEUE_H

#include <stddef.h>
#include "ep_osal_types.h"

int ep_queue_create(ep_queue_t **queue, size_t item_size, size_t depth);
int ep_queue_send(ep_queue_t *queue, const void *item, unsigned int timeout_ms);
int ep_queue_recv(ep_queue_t *queue, void *item, unsigned int timeout_ms);

#endif
