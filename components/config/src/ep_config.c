#include "ep_config.h"
#include "ep_osal_err.h"

int ep_config_init(void)
{
    return EP_OK;
}

int ep_config_set_int(const char *key, int value)
{
    (void)key;
    (void)value;
    return EP_ERR_UNSUPPORTED;
}

int ep_config_get_int(const char *key, int default_value)
{
    (void)key;
    return default_value;
}

int ep_config_set_bool(const char *key, int value)
{
    (void)key;
    (void)value;
    return EP_ERR_UNSUPPORTED;
}

int ep_config_get_bool(const char *key, int default_value)
{
    (void)key;
    return default_value;
}

int ep_config_set_string(const char *key, const char *value)
{
    (void)key;
    (void)value;
    return EP_ERR_UNSUPPORTED;
}

const char *ep_config_get_string(const char *key, const char *default_value)
{
    (void)key;
    return default_value;
}
