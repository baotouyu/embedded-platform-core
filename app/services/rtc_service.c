#include "rtc_service.h"

#include "ep_hal_rtc.h"
#include "ep_log.h"
#include "ep_osal_err.h"

int rtc_service_init(void)
{
    EP_LOGI("app", "rtc service ready");
    return EP_OK;
}

int rtc_service_get_time(ep_rtc_time_t *time)
{
    ep_rtc_t *rtc = 0;
    int rc;
    int close_rc;

    if (time == 0) {
        return EP_ERR_INVAL;
    }

    rc = ep_rtc_open(&rtc, "rtc");
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_rtc_get_time(rtc, time);
    close_rc = ep_rtc_close(rtc);
    if (rc != EP_OK) {
        return rc;
    }

    return close_rc;
}
