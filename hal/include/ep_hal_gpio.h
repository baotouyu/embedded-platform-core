#ifndef EP_HAL_GPIO_H
#define EP_HAL_GPIO_H

#include "ep_hal_types.h"

typedef enum {
    EP_GPIO_INPUT = 0,
    EP_GPIO_OUTPUT = 1
} ep_gpio_dir_e;

int ep_gpio_request(ep_gpio_t **gpio, const char *name);
int ep_gpio_set_direction(ep_gpio_t *gpio, ep_gpio_dir_e dir);
int ep_gpio_write(ep_gpio_t *gpio, int value);
int ep_gpio_read(ep_gpio_t *gpio, int *value);

#endif
