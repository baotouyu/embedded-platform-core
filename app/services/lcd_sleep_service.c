#include "lcd_sleep_service.h"

#include "ep_log.h"
#include "ep_osal_err.h"

int lcd_sleep_service_init(void)
{
    EP_LOGI("app", "lcd sleep service ready");
    return EP_OK;
}

int lcd_sleep_service_set_sleep(int sleep_enabled)
{
    (void)sleep_enabled;
    return EP_ERR_UNSUPPORTED;
}
