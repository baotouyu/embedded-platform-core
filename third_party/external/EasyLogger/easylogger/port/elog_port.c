#include "elog.h"
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_time.h"

#if defined(RT_USING_CONSOLE)
#include <rtthread.h>
#endif
#include <stdio.h>
#include <string.h>

#define ELOG_RT_CONSOLE_CHUNK_SIZE 96u

static ep_mutex_t *g_elog_output_lock;
static char g_elog_time[24];

ElogErrCode elog_port_init(void)
{
    if (g_elog_output_lock != 0) {
        return ELOG_NO_ERR;
    }

    if (ep_mutex_create(&g_elog_output_lock) != EP_OK) {
        return ELOG_NO_ERR;
    }

    return ELOG_NO_ERR;
}

void elog_port_deinit(void)
{
}

void elog_port_output(const char *log, size_t size)
{
#if defined(RT_USING_CONSOLE)
    size_t offset = 0u;

    while (offset < size) {
        char chunk[ELOG_RT_CONSOLE_CHUNK_SIZE + 1u];
        size_t chunk_size = size - offset;

        if (chunk_size > ELOG_RT_CONSOLE_CHUNK_SIZE) {
            chunk_size = ELOG_RT_CONSOLE_CHUNK_SIZE;
        }

        (void)memcpy(chunk, log + offset, chunk_size);
        chunk[chunk_size] = '\0';
        rt_kprintf("%s", chunk);
        offset += chunk_size;
    }
#else
    (void)fwrite(log, 1u, size, stdout);
    (void)fflush(stdout);
#endif
}

void elog_port_output_lock(void)
{
    if (g_elog_output_lock != 0) {
        (void)ep_mutex_lock(g_elog_output_lock);
    }
}

void elog_port_output_unlock(void)
{
    if (g_elog_output_lock != 0) {
        (void)ep_mutex_unlock(g_elog_output_lock);
    }
}

const char *elog_port_get_time(void)
{
    (void)snprintf(g_elog_time, sizeof(g_elog_time), "ms:%010llu", (unsigned long long)ep_time_now_ms());
    return g_elog_time;
}

const char *elog_port_get_p_info(void)
{
    return "";
}

const char *elog_port_get_t_info(void)
{
    return "";
}
