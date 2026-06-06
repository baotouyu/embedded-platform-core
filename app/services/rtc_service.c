#include "rtc_service.h"

#include "ep_log.h"
#include "ep_osal_err.h"

int rtc_service_init(void)
{
    EP_LOGI("app", "rtc service ready");
    return EP_OK;
}

int rtc_service_get_time(ep_rtc_time_t *time)
{
    (void)time;
    return EP_ERR_UNSUPPORTED;
}
