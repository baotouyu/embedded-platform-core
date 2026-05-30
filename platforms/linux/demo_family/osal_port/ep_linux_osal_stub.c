#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_queue.h"
#include "ep_osal_thread.h"

int ep_linux_osal_stub(void)
{
    return 0;
}

int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg)
{
    (void)name;
    (void)arg;

    if (thread == 0 || entry == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_thread_join(ep_thread_t *thread)
{
    if (thread == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_mutex_create(ep_mutex_t **mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_mutex_lock(ep_mutex_t *mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_mutex_unlock(ep_mutex_t *mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_queue_create(ep_queue_t **queue, size_t item_size, size_t depth)
{
    (void)item_size;
    (void)depth;

    if (queue == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_queue_send(ep_queue_t *queue, const void *item, unsigned int timeout_ms)
{
    (void)timeout_ms;

    if (queue == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_queue_recv(ep_queue_t *queue, void *item, unsigned int timeout_ms)
{
    (void)timeout_ms;

    if (queue == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}
