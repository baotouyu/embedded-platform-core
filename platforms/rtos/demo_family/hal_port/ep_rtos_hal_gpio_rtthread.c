#include "ep_hal_err.h"
#include "ep_hal_gpio.h"

#include <drivers/pin.h>
#include <rtthread.h>
#include <string.h>

struct ep_gpio {
    const char *pin_name;
    rt_base_t pin;
    ep_gpio_dir_e direction;
    int direction_set;
    int requested;
};

static ep_gpio_t g_gpio_table[] = {
    {"PD.3", -1, EP_GPIO_INPUT, 0, 0},
    {"PE.13", -1, EP_GPIO_INPUT, 0, 0},
};

static ep_gpio_t *ep_gpio_find_entry(const char *name)
{
    unsigned int i;

    if (name == 0) {
        return 0;
    }

    if (strcmp(name, "lcd_sleep_gpio") == 0) {
        return &g_gpio_table[0];
    }

    if (strcmp(name, "panel_enable_gpio") == 0) {
        return &g_gpio_table[1];
    }

    for (i = 0; i < sizeof(g_gpio_table) / sizeof(g_gpio_table[0]); ++i) {
        if (strcmp(name, g_gpio_table[i].pin_name) == 0) {
            return &g_gpio_table[i];
        }
    }

    return 0;
}

int ep_gpio_request(ep_gpio_t **gpio, const char *name)
{
    ep_gpio_t *entry;
    rt_base_t pin;

    if (gpio == 0 || name == 0) {
        return EP_ERR_INVAL;
    }
    *gpio = 0;

    entry = ep_gpio_find_entry(name);
    if (entry != 0) {
        if (entry->requested) {
            return EP_ERR_BUSY;
        }

        pin = rt_pin_get(entry->pin_name);
        if (pin < 0) {
            return EP_ERR_UNSUPPORTED;
        }

        entry->pin = pin;
        entry->direction = EP_GPIO_INPUT;
        entry->direction_set = 0;
        entry->requested = 1;
        *gpio = entry;
        return EP_OK;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_gpio_set_direction(ep_gpio_t *gpio, ep_gpio_dir_e dir)
{
    if (gpio == 0 || !gpio->requested) {
        return EP_ERR_INVAL;
    }

    switch (dir) {
    case EP_GPIO_INPUT:
        rt_pin_mode(gpio->pin, PIN_MODE_INPUT);
        break;
    case EP_GPIO_OUTPUT:
        rt_pin_mode(gpio->pin, PIN_MODE_OUTPUT);
        break;
    default:
        return EP_ERR_INVAL;
    }

    gpio->direction = dir;
    gpio->direction_set = 1;
    return EP_OK;
}

int ep_gpio_write(ep_gpio_t *gpio, int value)
{
    if (gpio == 0 || !gpio->requested || !gpio->direction_set || gpio->direction != EP_GPIO_OUTPUT) {
        return EP_ERR_INVAL;
    }

    rt_pin_write(gpio->pin, value == 0 ? PIN_LOW : PIN_HIGH);
    return EP_OK;
}

int ep_gpio_read(ep_gpio_t *gpio, int *value)
{
    if (gpio == 0 || !gpio->requested || value == 0) {
        return EP_ERR_INVAL;
    }

    *value = rt_pin_read(gpio->pin) == PIN_LOW ? 0 : 1;
    return EP_OK;
}
