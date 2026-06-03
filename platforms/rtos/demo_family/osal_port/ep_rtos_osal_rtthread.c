#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_mutex.h"
#include "ep_osal_queue.h"
#include "ep_osal_thread.h"
#include "ep_osal_time.h"

#include <rtthread.h>

struct ep_thread {
    rt_thread_t handle;
    ep_thread_entry_t entry;
    void *arg;
};

struct ep_mutex {
    rt_mutex_t handle;
};

struct ep_queue {
    rt_mq_t handle;
    rt_size_t item_size;
};

static int ep_rt_err_to_ep(rt_err_t rc)
{
    if (rc == RT_EOK) {
        return EP_OK;
    }

    if (rc == -RT_ETIMEOUT) {
        return EP_ERR_TIMEOUT;
    }

    if (rc == -RT_EFULL || rc == -RT_ENOMEM) {
        return EP_ERR_BUSY;
    }

    return EP_ERR_UNSUPPORTED;
}

void *ep_malloc(size_t size)
{
    return rt_malloc((rt_size_t)size);
}

void ep_free(void *ptr)
{
    rt_free(ptr);
}

uint64_t ep_time_now_ms(void)
{
    return (uint64_t)rt_tick_get_millisecond();
}

void ep_sleep_ms(unsigned int timeout_ms)
{
    (void)rt_thread_mdelay((rt_int32_t)timeout_ms);
}

static void ep_thread_trampoline(void *parameter)
{
    ep_thread_t *thread = (ep_thread_t *)parameter;

    if (thread != 0 && thread->entry != 0) {
        (void)thread->entry(thread->arg);
    }
}

int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg)
{
    ep_thread_t *new_thread;
    rt_thread_t handle;

    if (thread == 0 || entry == 0) {
        return EP_ERR_INVAL;
    }

    new_thread = (ep_thread_t *)ep_malloc(sizeof(*new_thread));
    if (new_thread == 0) {
        return EP_ERR_BUSY;
    }

    new_thread->entry = entry;
    new_thread->arg = arg;

    handle = rt_thread_create(name != 0 ? name : "ep", ep_thread_trampoline, new_thread, 4096, 20, 10);
    if (handle == RT_NULL) {
        ep_free(new_thread);
        return EP_ERR_BUSY;
    }

    if (rt_thread_startup(handle) != RT_EOK) {
        ep_free(new_thread);
        return EP_ERR_UNSUPPORTED;
    }

    new_thread->handle = handle;
    *thread = new_thread;
    return EP_OK;
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
    ep_mutex_t *new_mutex;
    rt_mutex_t handle;

    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    new_mutex = (ep_mutex_t *)ep_malloc(sizeof(*new_mutex));
    if (new_mutex == 0) {
        return EP_ERR_BUSY;
    }

    handle = rt_mutex_create("epm", RT_IPC_FLAG_FIFO);
    if (handle == RT_NULL) {
        ep_free(new_mutex);
        return EP_ERR_BUSY;
    }

    new_mutex->handle = handle;
    *mutex = new_mutex;
    return EP_OK;
}

int ep_mutex_lock(ep_mutex_t *mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    return ep_rt_err_to_ep(rt_mutex_take(mutex->handle, RT_WAITING_FOREVER));
}

int ep_mutex_unlock(ep_mutex_t *mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    return ep_rt_err_to_ep(rt_mutex_release(mutex->handle));
}

int ep_queue_create(ep_queue_t **queue, size_t item_size, size_t depth)
{
    ep_queue_t *new_queue;
    rt_mq_t handle;

    if (queue == 0 || item_size == 0u || depth == 0u || item_size > (size_t)((rt_size_t)-1)) {
        return EP_ERR_INVAL;
    }

    new_queue = (ep_queue_t *)ep_malloc(sizeof(*new_queue));
    if (new_queue == 0) {
        return EP_ERR_BUSY;
    }

    handle = rt_mq_create("epq", (rt_size_t)item_size, (rt_size_t)depth, RT_IPC_FLAG_FIFO);
    if (handle == RT_NULL) {
        ep_free(new_queue);
        return EP_ERR_BUSY;
    }

    new_queue->handle = handle;
    new_queue->item_size = (rt_size_t)item_size;
    *queue = new_queue;
    return EP_OK;
}

int ep_queue_send(ep_queue_t *queue, const void *item, unsigned int timeout_ms)
{
    if (queue == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    if (timeout_ms == 0u) {
        return ep_rt_err_to_ep(rt_mq_send(queue->handle, item, queue->item_size));
    }

    return ep_rt_err_to_ep(rt_mq_send_wait(queue->handle, item, queue->item_size, rt_tick_from_millisecond((rt_int32_t)timeout_ms)));
}

int ep_queue_recv(ep_queue_t *queue, void *item, unsigned int timeout_ms)
{
    rt_int32_t timeout;

    if (queue == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    timeout = timeout_ms == 0u ? RT_WAITING_NO : rt_tick_from_millisecond((rt_int32_t)timeout_ms);
    return ep_rt_err_to_ep(rt_mq_recv(queue->handle, item, queue->item_size, timeout));
}
