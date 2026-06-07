#include "ep_hal_gpio.h"
#include "ep_hal_pwm.h"
#include "ep_hal_rtc.h"
#include "ep_osal_err.h"

struct ep_gpio {
    int dummy;
};

static struct ep_gpio s_host_stub_gpio;

int ep_host_hal_stub_link_anchor(void)
{
    return 0;
}

int ep_pwm_open(ep_pwm_t **pwm, const char *name)
{
    if (pwm == 0 || name == 0) {
        return EP_ERR_INVAL;
    }

    *pwm = 0;
    return EP_ERR_UNSUPPORTED;
}

int ep_pwm_set(ep_pwm_t *pwm, unsigned int period_ns, unsigned int duty_ns)
{
    if (pwm == 0 || period_ns == 0u || duty_ns > period_ns) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_pwm_enable(ep_pwm_t *pwm)
{
    if (pwm == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_pwm_disable(ep_pwm_t *pwm)
{
    if (pwm == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_pwm_close(ep_pwm_t *pwm)
{
    if (pwm == 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_gpio_request(ep_gpio_t **gpio, const char *name)
{
    if (gpio == 0 || name == 0) {
        return EP_ERR_INVAL;
    }

    *gpio = &s_host_stub_gpio;
    return EP_OK;
}

int ep_gpio_set_direction(ep_gpio_t *gpio, ep_gpio_dir_e dir)
{
    if (gpio == 0 || (dir != EP_GPIO_INPUT && dir != EP_GPIO_OUTPUT)) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_gpio_write(ep_gpio_t *gpio, int value)
{
    if (gpio == 0) {
        return EP_ERR_INVAL;
    }

    (void)value;
    return EP_ERR_UNSUPPORTED;
}

int ep_gpio_read(ep_gpio_t *gpio, int *value)
{
    if (gpio == 0 || value == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_rtc_open(ep_rtc_t **rtc, const char *name)
{
    if (rtc == 0 || name == 0) {
        return EP_ERR_INVAL;
    }

    *rtc = 0;
    return EP_ERR_UNSUPPORTED;
}

int ep_rtc_get_time(ep_rtc_t *rtc, ep_rtc_time_t *time)
{
    if (rtc == 0 || time == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_rtc_set_time(ep_rtc_t *rtc, const ep_rtc_time_t *time)
{
    if (rtc == 0 || time == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_rtc_close(ep_rtc_t *rtc)
{
    if (rtc == 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}
