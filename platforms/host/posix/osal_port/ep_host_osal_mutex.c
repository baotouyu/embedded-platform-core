#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_mutex.h"

#include <pthread.h>

struct ep_mutex {
    pthread_mutex_t handle;
};

int ep_mutex_create(ep_mutex_t **mutex)
{
    ep_mutex_t *new_mutex;

    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    new_mutex = (ep_mutex_t *)ep_malloc(sizeof(*new_mutex));
    if (new_mutex == 0) {
        return EP_ERR_BUSY;
    }

    if (pthread_mutex_init(&new_mutex->handle, 0) != 0) {
        ep_free(new_mutex);
        return EP_ERR_UNSUPPORTED;
    }

    *mutex = new_mutex;
    return EP_OK;
}

int ep_mutex_lock(ep_mutex_t *mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    if (pthread_mutex_lock(&mutex->handle) != 0) {
        return EP_ERR_BUSY;
    }

    return EP_OK;
}

int ep_mutex_unlock(ep_mutex_t *mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    if (pthread_mutex_unlock(&mutex->handle) != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}
