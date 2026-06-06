#ifndef RTC_SERVICE_H
#define RTC_SERVICE_H

#include "ep_hal_rtc.h"

int rtc_service_init(void);
int rtc_service_get_time(ep_rtc_time_t *time);

#endif
