#ifndef EP_HAL_SPI_H
#define EP_HAL_SPI_H

#include <stddef.h>

#include "ep_hal_types.h"

int ep_spi_open(ep_spi_t **bus, const char *name);
int ep_spi_transfer(ep_spi_t *bus, const void *tx_buf, void *rx_buf, size_t len);

#endif
