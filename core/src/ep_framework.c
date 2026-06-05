#include "ep_framework.h"
#include "app_main.h"
#include "ep_log.h"
#include "ep_config.h"
#include "ep_device.h"
#include "ep_event.h"
#include "ep_timer.h"
#include "ep_osal_err.h"

#define EP_FRAMEWORK_DEFAULT_CONFIG_PATH "config/profiles/host.cfg"
#define EP_FRAMEWORK_LOG_LEVEL_KEY "log.level"

static int ep_framework_load_default_config(void)
{
    int rc = ep_config_load_file(EP_FRAMEWORK_DEFAULT_CONFIG_PATH);

    if (rc == EP_ERR_UNSUPPORTED) {
        return EP_OK;
    }

    return rc;
}

static int ep_framework_apply_log_config(void)
{
    int level = ep_config_get_int(EP_FRAMEWORK_LOG_LEVEL_KEY, EP_LOG_LEVEL_INFO);

    if (level < EP_LOG_LEVEL_ASSERT || level > EP_LOG_LEVEL_VERBOSE) {
        return EP_ERR_INVAL;
    }

    return ep_log_set_level((ep_log_level_e)level);
}

int ep_framework_init(void)
{
    int rc = ep_log_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_config_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_load_default_config();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_apply_log_config();
    if (rc != 0) {
        return rc;
    }

    rc = ep_event_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_timer_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_device_init();
    if (rc != 0) {
        return rc;
    }

    return ep_platform_register_default_devices();
}

int ep_framework_start(void)
{
    int rc = ep_platform_boot();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_init();
    if (rc != 0) {
        return rc;
    }

    return app_main();
}
