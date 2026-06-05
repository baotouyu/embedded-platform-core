#include "ep_hal_err.h"
#include "ep_hal_pwm.h"

#include <drivers/rt_drv_pwm.h>
#include <rtthread.h>
#include <string.h>

struct ep_pwm {
    struct rt_device_pwm *device;
    int channel;
};

static int ep_rtthread_pwm_ok(rt_err_t rc)
{
    return rc == RT_EOK ? EP_OK : EP_ERR_UNSUPPORTED;
}

static int ep_pwm_resolve(const char *name, const char **device_name, int *channel)
{
    if (name == 0 || device_name == 0 || channel == 0) {
        return EP_ERR_INVAL;
    }

    if (strcmp(name, "beep_pwm") == 0) {
        *device_name = "pwm";
        *channel = 1;
        return EP_OK;
    }

    if (strcmp(name, "pwm") == 0) {
        *device_name = "pwm";
        *channel = 1;
        return EP_OK;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_pwm_open(ep_pwm_t **pwm, const char *name)
{
    const char *device_name;
    int channel;
    rt_device_t device;
    ep_pwm_t *new_pwm;
    int rc;

    if (pwm == 0 || name == 0) {
        return EP_ERR_INVAL;
    }
    *pwm = 0;

    rc = ep_pwm_resolve(name, &device_name, &channel);
    if (rc != EP_OK) {
        return rc;
    }

    device = rt_device_find(device_name);
    if (device == RT_NULL) {
        return EP_ERR_UNSUPPORTED;
    }

    new_pwm = (ep_pwm_t *)rt_malloc((rt_size_t)sizeof(*new_pwm));
    if (new_pwm == 0) {
        return EP_ERR_BUSY;
    }

    new_pwm->device = (struct rt_device_pwm *)device;
    new_pwm->channel = channel;
    *pwm = new_pwm;
    return EP_OK;
}

int ep_pwm_set(ep_pwm_t *pwm, unsigned int period_ns, unsigned int duty_ns)
{
    if (pwm == 0 || period_ns == 0u || duty_ns > period_ns) {
        return EP_ERR_INVAL;
    }

    return ep_rtthread_pwm_ok(rt_pwm_set(pwm->device, pwm->channel, (rt_uint32_t)period_ns, (rt_uint32_t)duty_ns));
}

int ep_pwm_enable(ep_pwm_t *pwm)
{
    if (pwm == 0) {
        return EP_ERR_INVAL;
    }

    return ep_rtthread_pwm_ok(rt_pwm_enable(pwm->device, pwm->channel));
}

int ep_pwm_disable(ep_pwm_t *pwm)
{
    if (pwm == 0) {
        return EP_ERR_INVAL;
    }

    return ep_rtthread_pwm_ok(rt_pwm_disable(pwm->device, pwm->channel));
}

int ep_pwm_close(ep_pwm_t *pwm)
{
    if (pwm == 0) {
        return EP_ERR_INVAL;
    }

    rt_free(pwm);
    return EP_OK;
}
