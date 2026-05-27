#ifndef EP_OSAL_THREAD_H
#define EP_OSAL_THREAD_H

#include "ep_osal_types.h"

typedef void *(*ep_thread_entry_t)(void *arg);

int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg);
int ep_thread_join(ep_thread_t *thread);

#endif
