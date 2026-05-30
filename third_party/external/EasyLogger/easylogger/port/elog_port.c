#include "elog.h"
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_time.h"

#include <stdio.h>

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
    (void)fwrite(log, 1u, size, stdout);
    (void)fflush(stdout);
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
