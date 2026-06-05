#ifndef EP_HAL_RTC_H
#define EP_HAL_RTC_H

#include <stdint.h>

#include "ep_hal_types.h"

typedef struct {
    uint16_t year;
    uint8_t month;
    uint8_t day;
    uint8_t hour;
    uint8_t minute;
    uint8_t second;
    uint8_t weekday;
} ep_rtc_time_t;

int ep_rtc_open(ep_rtc_t **rtc, const char *name);
int ep_rtc_get_time(ep_rtc_t *rtc, ep_rtc_time_t *time);
int ep_rtc_set_time(ep_rtc_t *rtc, const ep_rtc_time_t *time);
int ep_rtc_close(ep_rtc_t *rtc);

#endif
