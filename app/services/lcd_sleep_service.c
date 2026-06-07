#include "lcd_sleep_service.h"

#include "ep_hal_gpio.h"
#include "ep_log.h"
#include "ep_osal_err.h"

static ep_gpio_t *s_lcd_sleep_gpio;
static int s_lcd_sleep_ready;

int lcd_sleep_service_init(void)
{
    int rc;

    if (s_lcd_sleep_ready) {
        return EP_OK;
    }

    rc = ep_gpio_request(&s_lcd_sleep_gpio, "lcd_sleep_gpio");
    if (rc != EP_OK) {
        s_lcd_sleep_gpio = 0;
        return rc;
    }

    rc = ep_gpio_set_direction(s_lcd_sleep_gpio, EP_GPIO_OUTPUT);
    if (rc != EP_OK) {
        s_lcd_sleep_gpio = 0;
        return rc;
    }

    s_lcd_sleep_ready = 1;
    EP_LOGI("app", "lcd sleep service ready");
    return EP_OK;
}

int lcd_sleep_service_set_sleep(int sleep_enabled)
{
    int rc;

    if (!s_lcd_sleep_ready) {
        rc = lcd_sleep_service_init();
        if (rc != EP_OK) {
            return rc;
        }
    }

    return ep_gpio_write(s_lcd_sleep_gpio, sleep_enabled ? 1 : 0);
}
