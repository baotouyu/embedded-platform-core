#include "ep_hal_err.h"
#include "ep_hal_rtc.h"

#include <drivers/i2c.h>
#include <rtthread.h>
#include <string.h>

#define EP_PCF8563_I2C_ADDR 0x51u
#define EP_PCF8563_TIME_REG 0x02u
#define EP_PCF8563_TIME_LEN 7u
#define EP_PCF8563_VL_BIT 0x80u

struct ep_rtc {
    struct rt_i2c_bus_device *bus;
};

static int ep_rtc_resolve_bus_name(const char *name, const char **bus_name)
{
    if (name == 0 || bus_name == 0) {
        return EP_ERR_INVAL;
    }

    if (strcmp(name, "rtc") == 0 || strcmp(name, "pcf8563") == 0) {
        *bus_name = "i2c1";
        return EP_OK;
    }

    return EP_ERR_UNSUPPORTED;
}

static uint8_t ep_pcf8563_to_bcd(uint8_t value)
{
    return (uint8_t)(((value / 10u) << 4u) | (value % 10u));
}

static uint8_t ep_pcf8563_from_bcd(uint8_t value)
{
    return (uint8_t)(((value >> 4u) * 10u) + (value & 0x0fu));
}

static int ep_pcf8563_transfer(struct ep_rtc *rtc, struct rt_i2c_msg *msg)
{
    return rt_i2c_transfer(rtc->bus, msg, 1) == 1 ? EP_OK : EP_ERR_UNSUPPORTED;
}

static int ep_pcf8563_validate_time(const ep_rtc_time_t *time)
{
    if (time == 0) {
        return EP_ERR_INVAL;
    }

    if (time->year < 2000u || time->year > 2099u ||
        time->month < 1u || time->month > 12u ||
        time->day < 1u || time->day > 31u ||
        time->hour > 23u ||
        time->minute > 59u ||
        time->second > 59u ||
        time->weekday > 6u) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_rtc_open(ep_rtc_t **rtc, const char *name)
{
    const char *bus_name;
    struct rt_i2c_bus_device *bus;
    ep_rtc_t *new_rtc;
    int rc;

    if (rtc == 0 || name == 0) {
        return EP_ERR_INVAL;
    }
    *rtc = 0;

    rc = ep_rtc_resolve_bus_name(name, &bus_name);
    if (rc != EP_OK) {
        return rc;
    }

    bus = rt_i2c_bus_device_find(bus_name);
    if (bus == RT_NULL) {
        return EP_ERR_UNSUPPORTED;
    }

    new_rtc = (ep_rtc_t *)rt_malloc((rt_size_t)sizeof(*new_rtc));
    if (new_rtc == 0) {
        return EP_ERR_BUSY;
    }

    new_rtc->bus = bus;
    *rtc = new_rtc;
    return EP_OK;
}

int ep_rtc_get_time(ep_rtc_t *rtc, ep_rtc_time_t *time)
{
    uint8_t reg = EP_PCF8563_TIME_REG;
    uint8_t data[EP_PCF8563_TIME_LEN];
    struct rt_i2c_msg msg;
    int rc;

    if (rtc == 0 || time == 0) {
        return EP_ERR_INVAL;
    }

    msg.addr = EP_PCF8563_I2C_ADDR;
    msg.flags = RT_I2C_WR;
    msg.len = 1u;
    msg.buf = &reg;
    rc = ep_pcf8563_transfer(rtc, &msg);
    if (rc != EP_OK) {
        return rc;
    }

    msg.addr = EP_PCF8563_I2C_ADDR;
    msg.flags = RT_I2C_RD;
    msg.len = EP_PCF8563_TIME_LEN;
    msg.buf = data;
    rc = ep_pcf8563_transfer(rtc, &msg);
    if (rc != EP_OK) {
        return rc;
    }

    if ((data[0] & EP_PCF8563_VL_BIT) != 0u) {
        return EP_ERR_UNSUPPORTED;
    }

    time->second = ep_pcf8563_from_bcd((uint8_t)(data[0] & 0x7fu));
    time->minute = ep_pcf8563_from_bcd((uint8_t)(data[1] & 0x7fu));
    time->hour = ep_pcf8563_from_bcd((uint8_t)(data[2] & 0x3fu));
    time->day = ep_pcf8563_from_bcd((uint8_t)(data[3] & 0x3fu));
    time->weekday = (uint8_t)(data[4] & 0x07u);
    time->month = ep_pcf8563_from_bcd((uint8_t)(data[5] & 0x1fu));
    time->year = (uint16_t)(2000u + ep_pcf8563_from_bcd(data[6]));

    return ep_pcf8563_validate_time(time);
}

int ep_rtc_set_time(ep_rtc_t *rtc, const ep_rtc_time_t *time)
{
    uint8_t data[1u + EP_PCF8563_TIME_LEN];
    struct rt_i2c_msg msg;
    int rc;

    if (rtc == 0) {
        return EP_ERR_INVAL;
    }

    rc = ep_pcf8563_validate_time(time);
    if (rc != EP_OK) {
        return rc;
    }

    data[0] = EP_PCF8563_TIME_REG;
    data[1] = ep_pcf8563_to_bcd(time->second);
    data[2] = ep_pcf8563_to_bcd(time->minute);
    data[3] = ep_pcf8563_to_bcd(time->hour);
    data[4] = ep_pcf8563_to_bcd(time->day);
    data[5] = ep_pcf8563_to_bcd(time->weekday);
    data[6] = ep_pcf8563_to_bcd(time->month);
    data[7] = ep_pcf8563_to_bcd((uint8_t)(time->year - 2000u));

    msg.addr = EP_PCF8563_I2C_ADDR;
    msg.flags = RT_I2C_WR;
    msg.len = (rt_uint16_t)sizeof(data);
    msg.buf = data;
    return ep_pcf8563_transfer(rtc, &msg);
}

int ep_rtc_close(ep_rtc_t *rtc)
{
    if (rtc == 0) {
        return EP_ERR_INVAL;
    }

    rt_free(rtc);
    return EP_OK;
}
