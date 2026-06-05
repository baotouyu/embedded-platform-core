#include "ep_hal_err.h"
#include "ep_hal_uart.h"

#include <rtthread.h>
#include <string.h>

struct ep_uart {
    rt_device_t device;
};

static const char *ep_uart_resolve_device_name(const char *name)
{
    if (name == 0) {
        return 0;
    }

    if (strcmp(name, "console_uart") == 0) {
        return "uart1";
    }

    if (strcmp(name, "power_uart") == 0) {
        return "uart2";
    }

    return name;
}

int ep_uart_open(ep_uart_t **uart, const char *name)
{
    const char *device_name;
    rt_device_t device;
    ep_uart_t *new_uart;

    if (uart == 0 || name == 0) {
        return EP_ERR_INVAL;
    }
    *uart = 0;

    device_name = ep_uart_resolve_device_name(name);
    if (device_name == 0 || device_name[0] == '\0') {
        return EP_ERR_INVAL;
    }

    device = rt_device_find(device_name);
    if (device == RT_NULL) {
        return EP_ERR_UNSUPPORTED;
    }

    new_uart = (ep_uart_t *)rt_malloc((rt_size_t)sizeof(*new_uart));
    if (new_uart == 0) {
        return EP_ERR_BUSY;
    }

    if (rt_device_open(device, RT_DEVICE_OFLAG_RDWR | RT_DEVICE_FLAG_INT_RX | RT_DEVICE_FLAG_STREAM) != RT_EOK) {
        rt_free(new_uart);
        return EP_ERR_BUSY;
    }

    new_uart->device = device;
    *uart = new_uart;
    return EP_OK;
}

int ep_uart_write(ep_uart_t *uart, const void *buf, size_t len)
{
    rt_size_t written;

    if (uart == 0 || buf == 0) {
        return EP_ERR_INVAL;
    }

    if (len == 0u) {
        return EP_OK;
    }

    written = rt_device_write(uart->device, 0, buf, (rt_size_t)len);
    return written == (rt_size_t)len ? EP_OK : EP_ERR_BUSY;
}

int ep_uart_read(ep_uart_t *uart, void *buf, size_t len, unsigned int timeout_ms)
{
    rt_size_t received;
    rt_size_t total = 0;
    unsigned int waited_ms = 0;
    char *cursor;

    if (uart == 0 || buf == 0) {
        return EP_ERR_INVAL;
    }

    if (len == 0u) {
        return EP_OK;
    }

    cursor = (char *)buf;
    do {
        received = rt_device_read(uart->device, 0, cursor + total, (rt_size_t)len - total);
        total += received;
        if (total == (rt_size_t)len) {
            return EP_OK;
        }

        if (timeout_ms == 0u) {
            break;
        }

        (void)rt_thread_mdelay(1);
        ++waited_ms;
    } while (waited_ms < timeout_ms);

    return EP_ERR_TIMEOUT;
}

int ep_uart_close(ep_uart_t *uart)
{
    rt_err_t rc;

    if (uart == 0) {
        return EP_ERR_INVAL;
    }

    rc = rt_device_close(uart->device);
    rt_free(uart);
    return rc == RT_EOK ? EP_OK : EP_ERR_UNSUPPORTED;
}
