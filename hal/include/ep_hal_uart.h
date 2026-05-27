#ifndef EP_HAL_UART_H
#define EP_HAL_UART_H

#include <stddef.h>

#include "ep_hal_types.h"

int ep_uart_open(ep_uart_t **uart, const char *name);
int ep_uart_write(ep_uart_t *uart, const void *buf, size_t len);
int ep_uart_read(ep_uart_t *uart, void *buf, size_t len, unsigned int timeout_ms);
int ep_uart_close(ep_uart_t *uart);

#endif
