#include "ep_hal_err.h"
#include "ep_hal_i2c.h"

#include <drivers/i2c.h>
#include <rtthread.h>
#include <string.h>

struct ep_i2c {
    struct rt_i2c_bus_device *bus;
};

static ep_i2c_t g_i2c1 = {0};

static const char *ep_i2c_resolve_bus_name(const char *name)
{
    if (name == 0) {
        return 0;
    }

    if (strcmp(name, "rtc_bus") == 0) {
        return "i2c1";
    }

    if (strcmp(name, "i2c1") == 0) {
        return "i2c1";
    }

    return 0;
}

int ep_i2c_open(ep_i2c_t **bus, const char *name)
{
    const char *bus_name;
    struct rt_i2c_bus_device *rt_bus;

    if (bus == 0 || name == 0) {
        return EP_ERR_INVAL;
    }
    *bus = 0;

    bus_name = ep_i2c_resolve_bus_name(name);
    if (bus_name == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    rt_bus = rt_i2c_bus_device_find(bus_name);
    if (rt_bus == RT_NULL) {
        return EP_ERR_UNSUPPORTED;
    }

    g_i2c1.bus = rt_bus;
    *bus = &g_i2c1;
    return EP_OK;
}

int ep_i2c_write(ep_i2c_t *bus, uint16_t addr, const void *buf, size_t len)
{
    struct rt_i2c_msg msg;

    if (bus == 0 || (buf == 0 && len > 0u)) {
        return EP_ERR_INVAL;
    }

    if (len == 0u) {
        return EP_OK;
    }

    msg.addr = (rt_uint16_t)addr;
    msg.flags = RT_I2C_WR;
    msg.len = (rt_uint16_t)len;
    msg.buf = (rt_uint8_t *)buf;

    return rt_i2c_transfer(bus->bus, &msg, 1) == 1 ? EP_OK : EP_ERR_UNSUPPORTED;
}

int ep_i2c_read(ep_i2c_t *bus, uint16_t addr, void *buf, size_t len)
{
    struct rt_i2c_msg msg;

    if (bus == 0 || (buf == 0 && len > 0u)) {
        return EP_ERR_INVAL;
    }

    if (len == 0u) {
        return EP_OK;
    }

    msg.addr = (rt_uint16_t)addr;
    msg.flags = RT_I2C_RD;
    msg.len = (rt_uint16_t)len;
    msg.buf = (rt_uint8_t *)buf;

    return rt_i2c_transfer(bus->bus, &msg, 1) == 1 ? EP_OK : EP_ERR_UNSUPPORTED;
}
