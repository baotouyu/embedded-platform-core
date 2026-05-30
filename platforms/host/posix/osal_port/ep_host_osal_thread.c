#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_thread.h"

#include <pthread.h>

struct ep_thread {
    pthread_t handle;
};

int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg)
{
    ep_thread_t *new_thread;

    (void)name;

    if (thread == 0 || entry == 0) {
        return EP_ERR_INVAL;
    }

    new_thread = (ep_thread_t *)ep_malloc(sizeof(*new_thread));
    if (new_thread == 0) {
        return EP_ERR_BUSY;
    }

    if (pthread_create(&new_thread->handle, 0, entry, arg) != 0) {
        ep_free(new_thread);
        return EP_ERR_UNSUPPORTED;
    }

    *thread = new_thread;
    return EP_OK;
}

int ep_thread_join(ep_thread_t *thread)
{
    if (thread == 0) {
        return EP_ERR_INVAL;
    }

    if (pthread_join(thread->handle, 0) != 0) {
        return EP_ERR_INVAL;
    }

    ep_free(thread);
    return EP_OK;
}
