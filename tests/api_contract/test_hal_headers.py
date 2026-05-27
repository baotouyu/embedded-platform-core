from pathlib import Path


def test_hal_headers_expose_ep_handle_api():
    uart = Path("hal/include/ep_hal_uart.h").read_text()
    gpio = Path("hal/include/ep_hal_gpio.h").read_text()
    assert "ep_uart_t" in uart
    assert "ep_uart_open" in uart
    assert "ep_gpio_t" in gpio
    assert "ep_gpio_write" in gpio
