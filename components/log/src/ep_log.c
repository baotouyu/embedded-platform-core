#include "ep_log.h"
#include "ep_osal_err.h"
#include "elog.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>

#define EP_LOG_LINE_BUF_SIZE 256u

static int g_ep_log_initialized;
static ep_log_level_e g_ep_log_level = EP_LOG_LEVEL_INFO;

static int ep_log_level_is_valid(ep_log_level_e level)
{
    return level >= EP_LOG_LEVEL_ASSERT && level <= EP_LOG_LEVEL_VERBOSE;
}

static int ep_log_to_easylogger_level(ep_log_level_e level, uint8_t *elog_level)
{
    if (elog_level == 0) {
        return EP_ERR_INVAL;
    }

    switch (level) {
    case EP_LOG_LEVEL_ASSERT:
        *elog_level = ELOG_LVL_ASSERT;
        return EP_OK;
    case EP_LOG_LEVEL_ERROR:
        *elog_level = ELOG_LVL_ERROR;
        return EP_OK;
    case EP_LOG_LEVEL_WARN:
        *elog_level = ELOG_LVL_WARN;
        return EP_OK;
    case EP_LOG_LEVEL_INFO:
        *elog_level = ELOG_LVL_INFO;
        return EP_OK;
    case EP_LOG_LEVEL_DEBUG:
        *elog_level = ELOG_LVL_DEBUG;
        return EP_OK;
    case EP_LOG_LEVEL_VERBOSE:
        *elog_level = ELOG_LVL_VERBOSE;
        return EP_OK;
    default:
        return EP_ERR_INVAL;
    }
}

int ep_log_init(void)
{
    ElogErrCode rc;

    if (g_ep_log_initialized != 0) {
        return EP_OK;
    }

    rc = elog_init();
    if (rc != ELOG_NO_ERR) {
        return EP_ERR_UNSUPPORTED;
    }

    elog_set_fmt(ELOG_LVL_ASSERT, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME | ELOG_FMT_DIR | ELOG_FMT_LINE);
    elog_set_fmt(ELOG_LVL_ERROR, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
    elog_set_fmt(ELOG_LVL_WARN, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
    elog_set_fmt(ELOG_LVL_INFO, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
    elog_set_fmt(ELOG_LVL_DEBUG, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME | ELOG_FMT_DIR | ELOG_FMT_LINE);
    elog_set_fmt(ELOG_LVL_VERBOSE, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
    elog_start();

    g_ep_log_initialized = 1;
    return EP_OK;
}

int ep_log_set_level(ep_log_level_e level)
{
    if (!ep_log_level_is_valid(level)) {
        return EP_ERR_INVAL;
    }

    g_ep_log_level = level;
    return EP_OK;
}

ep_log_level_e ep_log_get_level(void)
{
    return g_ep_log_level;
}

int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...)
{
    char line[EP_LOG_LINE_BUF_SIZE];
    uint8_t elog_level;
    va_list args;
    int rc;

    if (g_ep_log_initialized == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    if (tag == 0 || fmt == 0) {
        return EP_ERR_INVAL;
    }

    rc = ep_log_to_easylogger_level(level, &elog_level);
    if (rc != EP_OK) {
        return rc;
    }

    if (level > g_ep_log_level) {
        return EP_OK;
    }

    va_start(args, fmt);
    (void)vsnprintf(line, sizeof(line), fmt, args);
    va_end(args);

    elog_output(elog_level, tag, 0, 0, 0, "%s", line);
    return EP_OK;
}
