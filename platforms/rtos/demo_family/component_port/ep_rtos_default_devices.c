#include "ep_device.h"
#include "ep_framework.h"
#include "ep_osal_err.h"

static int ep_register_default_device(const char *name,
                                      ep_device_type_e type,
                                      ep_platform_capability_e capability)
{
    ep_device_desc_t desc;
    int rc;

    if (ep_device_find(name) != 0) {
        return EP_OK;
    }

    desc.name = name;
    desc.type = type;
    desc.state = EP_DEVICE_STATE_ONLINE;
    desc.capability = capability;
    desc.context = 0;

    rc = ep_device_register(&desc, 0);
    return rc == EP_ERR_BUSY && ep_device_find(name) != 0 ? EP_OK : rc;
}

int ep_platform_register_default_devices(void)
{
    int rc;

    rc = ep_register_default_device("console_uart", EP_DEVICE_TYPE_UART, EP_PLATFORM_CAPABILITY_UART);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_register_default_device("power_uart", EP_DEVICE_TYPE_UART, EP_PLATFORM_CAPABILITY_UART);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_register_default_device("beep_pwm", EP_DEVICE_TYPE_OTHER, EP_PLATFORM_CAPABILITY_PWM);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_register_default_device("rtc_bus", EP_DEVICE_TYPE_I2C, EP_PLATFORM_CAPABILITY_I2C);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_register_default_device("lcd_sleep_gpio", EP_DEVICE_TYPE_GPIO, EP_PLATFORM_CAPABILITY_GPIO);
    if (rc != EP_OK) {
        return rc;
    }

    return ep_register_default_device("panel_enable_gpio", EP_DEVICE_TYPE_GPIO, EP_PLATFORM_CAPABILITY_GPIO);
}
