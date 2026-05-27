#ifndef EP_OSAL_SEM_H
#define EP_OSAL_SEM_H

#include "ep_osal_types.h"

int ep_sem_create(ep_sem_t **sem, unsigned int initial_count);
int ep_sem_wait(ep_sem_t *sem, unsigned int timeout_ms);
int ep_sem_post(ep_sem_t *sem);

#endif
