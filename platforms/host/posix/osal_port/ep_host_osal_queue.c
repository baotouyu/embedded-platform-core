#if !defined(__APPLE__)
#define _POSIX_C_SOURCE 200809L
#endif

#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_queue.h"

#include <errno.h>
#include <pthread.h>
#include <stddef.h>
#include <string.h>
#include <sys/time.h>
#include <time.h>

struct ep_queue {
    pthread_mutex_t lock;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
    unsigned char *buffer;
    size_t item_size;
    size_t depth;
    size_t head;
    size_t tail;
    size_t count;
};

static int ep_queue_init_cond(pthread_cond_t *cond)
{
#if defined(__APPLE__)
    return pthread_cond_init(cond, 0);
#else
    pthread_condattr_t attr;
    int rc;

    rc = pthread_condattr_init(&attr);
    if (rc != 0) {
        return rc;
    }

    rc = pthread_condattr_setclock(&attr, CLOCK_MONOTONIC);
    if (rc != 0) {
        (void)pthread_condattr_destroy(&attr);
        return rc;
    }

    rc = pthread_cond_init(cond, &attr);
    if (pthread_condattr_destroy(&attr) != 0 && rc == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    return rc;
#endif
}

static int ep_queue_make_deadline(struct timespec *deadline, unsigned int timeout_ms)
{
#if defined(__APPLE__)
    struct timeval now;
    long nsec;

    if (gettimeofday(&now, 0) != 0) {
        return EP_ERR_UNSUPPORTED;
    }

    deadline->tv_sec = now.tv_sec + (time_t)(timeout_ms / 1000u);
    nsec = ((long)now.tv_usec * 1000L) + ((long)(timeout_ms % 1000u) * 1000000L);
    deadline->tv_sec += (time_t)(nsec / 1000000000L);
    deadline->tv_nsec = nsec % 1000000000L;
#else
    long nsec;

    if (clock_gettime(CLOCK_MONOTONIC, deadline) != 0) {
        return EP_ERR_UNSUPPORTED;
    }

    deadline->tv_sec += (time_t)(timeout_ms / 1000u);
    nsec = deadline->tv_nsec + ((long)(timeout_ms % 1000u) * 1000000L);
    deadline->tv_sec += (time_t)(nsec / 1000000000L);
    deadline->tv_nsec = nsec % 1000000000L;
#endif

    return EP_OK;
}

static int ep_queue_init_sync(ep_queue_t *queue)
{
    int rc;

    rc = pthread_mutex_init(&queue->lock, 0);
    if (rc != 0) {
        return EP_ERR_UNSUPPORTED;
    }

    rc = ep_queue_init_cond(&queue->not_empty);
    if (rc != 0) {
        (void)pthread_mutex_destroy(&queue->lock);
        return EP_ERR_UNSUPPORTED;
    }

    rc = ep_queue_init_cond(&queue->not_full);
    if (rc != 0) {
        (void)pthread_cond_destroy(&queue->not_empty);
        (void)pthread_mutex_destroy(&queue->lock);
        return EP_ERR_UNSUPPORTED;
    }

    return EP_OK;
}

static unsigned char *ep_queue_slot(ep_queue_t *queue, size_t index)
{
    return queue->buffer + (index * queue->item_size);
}

int ep_queue_create(ep_queue_t **queue, size_t item_size, size_t depth)
{
    ep_queue_t *new_queue;
    int rc;

    if (queue == 0 || item_size == 0u || depth == 0u) {
        return EP_ERR_INVAL;
    }

    if (depth > ((size_t)-1) / item_size) {
        return EP_ERR_INVAL;
    }

    new_queue = (ep_queue_t *)ep_malloc(sizeof(*new_queue));
    if (new_queue == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    new_queue->buffer = (unsigned char *)ep_malloc(item_size * depth);
    if (new_queue->buffer == 0) {
        ep_free(new_queue);
        return EP_ERR_UNSUPPORTED;
    }

    new_queue->item_size = item_size;
    new_queue->depth = depth;
    new_queue->head = 0u;
    new_queue->tail = 0u;
    new_queue->count = 0u;

    rc = ep_queue_init_sync(new_queue);
    if (rc != EP_OK) {
        ep_free(new_queue->buffer);
        ep_free(new_queue);
        return rc;
    }

    *queue = new_queue;

    return EP_OK;
}

int ep_queue_send(ep_queue_t *queue, const void *item, unsigned int timeout_ms)
{
    struct timespec deadline;
    int rc;

    if (queue == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    rc = pthread_mutex_lock(&queue->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    if (queue->count == queue->depth && timeout_ms > 0u) {
        rc = ep_queue_make_deadline(&deadline, timeout_ms);
        if (rc != EP_OK) {
            (void)pthread_mutex_unlock(&queue->lock);
            return rc;
        }
    }

    while (queue->count == queue->depth) {
        if (timeout_ms == 0u) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_TIMEOUT;
        }

        rc = pthread_cond_timedwait(&queue->not_full, &queue->lock, &deadline);
        if (rc == ETIMEDOUT) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_TIMEOUT;
        }
        if (rc != 0) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_UNSUPPORTED;
        }
    }

    memcpy(ep_queue_slot(queue, queue->tail), item, queue->item_size);
    queue->tail = (queue->tail + 1u) % queue->depth;
    queue->count += 1u;

    rc = pthread_cond_signal(&queue->not_empty);
    if (rc != 0) {
        (void)pthread_mutex_unlock(&queue->lock);
        return EP_ERR_UNSUPPORTED;
    }

    rc = pthread_mutex_unlock(&queue->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_queue_recv(ep_queue_t *queue, void *item, unsigned int timeout_ms)
{
    struct timespec deadline;
    int rc;

    if (queue == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    rc = pthread_mutex_lock(&queue->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    if (queue->count == 0u && timeout_ms > 0u) {
        rc = ep_queue_make_deadline(&deadline, timeout_ms);
        if (rc != EP_OK) {
            (void)pthread_mutex_unlock(&queue->lock);
            return rc;
        }
    }

    while (queue->count == 0u) {
        if (timeout_ms == 0u) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_TIMEOUT;
        }

        rc = pthread_cond_timedwait(&queue->not_empty, &queue->lock, &deadline);
        if (rc == ETIMEDOUT) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_TIMEOUT;
        }
        if (rc != 0) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_UNSUPPORTED;
        }
    }

    memcpy(item, ep_queue_slot(queue, queue->head), queue->item_size);
    queue->head = (queue->head + 1u) % queue->depth;
    queue->count -= 1u;

    rc = pthread_cond_signal(&queue->not_full);
    if (rc != 0) {
        (void)pthread_mutex_unlock(&queue->lock);
        return EP_ERR_UNSUPPORTED;
    }

    rc = pthread_mutex_unlock(&queue->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}
