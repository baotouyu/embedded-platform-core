#if !defined(__APPLE__)
#define _POSIX_C_SOURCE 200809L
#endif

#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_sem.h"

#include <errno.h>
#include <pthread.h>
#include <sys/time.h>
#include <time.h>

struct ep_sem {
    pthread_mutex_t lock;
    pthread_cond_t cond;
    unsigned int count;
};

static int ep_sem_init_cond(pthread_cond_t *cond)
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

static int ep_sem_make_deadline(struct timespec *deadline, unsigned int timeout_ms)
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

int ep_sem_create(ep_sem_t **sem, unsigned int initial_count)
{
    ep_sem_t *new_sem;
    int rc;

    if (sem == 0) {
        return EP_ERR_INVAL;
    }

    new_sem = (ep_sem_t *)ep_malloc(sizeof(*new_sem));
    if (new_sem == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    rc = pthread_mutex_init(&new_sem->lock, 0);
    if (rc != 0) {
        ep_free(new_sem);
        return EP_ERR_UNSUPPORTED;
    }

    rc = ep_sem_init_cond(&new_sem->cond);
    if (rc != 0) {
        (void)pthread_mutex_destroy(&new_sem->lock);
        ep_free(new_sem);
        return EP_ERR_UNSUPPORTED;
    }

    new_sem->count = initial_count;
    *sem = new_sem;

    return EP_OK;
}

int ep_sem_wait(ep_sem_t *sem, unsigned int timeout_ms)
{
    struct timespec deadline;
    int rc;

    if (sem == 0) {
        return EP_ERR_INVAL;
    }

    rc = pthread_mutex_lock(&sem->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    if (sem->count == 0 && timeout_ms > 0u) {
        rc = ep_sem_make_deadline(&deadline, timeout_ms);
        if (rc != EP_OK) {
            (void)pthread_mutex_unlock(&sem->lock);
            return rc;
        }
    }

    while (sem->count == 0) {
        if (timeout_ms == 0u) {
            (void)pthread_mutex_unlock(&sem->lock);
            return EP_ERR_TIMEOUT;
        }

        rc = pthread_cond_timedwait(&sem->cond, &sem->lock, &deadline);
        if (rc == ETIMEDOUT) {
            (void)pthread_mutex_unlock(&sem->lock);
            return EP_ERR_TIMEOUT;
        }
        if (rc != 0) {
            (void)pthread_mutex_unlock(&sem->lock);
            return EP_ERR_UNSUPPORTED;
        }
    }

    sem->count -= 1u;

    rc = pthread_mutex_unlock(&sem->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_sem_post(ep_sem_t *sem)
{
    int signal_rc;
    int unlock_rc;
    int rc;

    if (sem == 0) {
        return EP_ERR_INVAL;
    }

    rc = pthread_mutex_lock(&sem->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    sem->count += 1u;
    signal_rc = pthread_cond_signal(&sem->cond);
    unlock_rc = pthread_mutex_unlock(&sem->lock);

    if (signal_rc != 0) {
        return EP_ERR_UNSUPPORTED;
    }
    if (unlock_rc != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}
