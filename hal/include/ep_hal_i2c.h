#ifndef EP_HAL_I2C_H
#define EP_HAL_I2C_H

#include <stddef.h>
#include <stdint.h>

#include "ep_hal_types.h"

int ep_i2c_open(ep_i2c_t **bus, const char *name);
int ep_i2c_write(ep_i2c_t *bus, uint16_t addr, const void *buf, size_t len);
int ep_i2c_read(ep_i2c_t *bus, uint16_t addr, void *buf, size_t len);

#endif
