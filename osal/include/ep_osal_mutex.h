#ifndef EP_OSAL_MUTEX_H
#define EP_OSAL_MUTEX_H

#include "ep_osal_types.h"

int ep_mutex_create(ep_mutex_t **mutex);
int ep_mutex_lock(ep_mutex_t *mutex);
int ep_mutex_unlock(ep_mutex_t *mutex);

#endif
