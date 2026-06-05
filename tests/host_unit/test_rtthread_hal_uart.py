import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_rtthread_hal_uart_maps_logical_names_to_rt_devices(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtthread_hal_uart_smoke.c"
    executable = tmp_path / "rtthread_hal_uart_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_hal_err.h"
            #include "ep_hal_uart.h"
            #include "rtthread.h"

            #include <string.h>

            int main(void)
            {
                ep_uart_t *uart = 0;
                ep_uart_t *console = 0;
                char rx[4] = {0};

                if (ep_uart_open(0, "power_uart") == EP_OK) {
                    return 1;
                }

                uart = (ep_uart_t *)1;
                if (ep_uart_open(&uart, "missing_uart") == EP_OK) {
                    return 2;
                }

                if (uart != 0) {
                    return 3;
                }

                if (ep_uart_open(&uart, "power_uart") != EP_OK) {
                    return 4;
                }

                if (fake_rt_last_find_name()[0] != 'u' || fake_rt_last_find_name()[4] != '2') {
                    return 5;
                }

                if ((fake_rt_last_open_flags() & RT_DEVICE_OFLAG_RDWR) == 0) {
                    return 6;
                }

                if ((fake_rt_last_open_flags() & RT_DEVICE_FLAG_INT_RX) == 0) {
                    return 7;
                }

                if ((fake_rt_last_open_flags() & RT_DEVICE_FLAG_STREAM) == 0) {
                    return 8;
                }

                if (ep_uart_write(uart, "OK", 2) != EP_OK) {
                    return 9;
                }

                if (strcmp(fake_rt_last_write(), "OK") != 0) {
                    return 10;
                }

                fake_rt_set_read_data("AB");
                if (ep_uart_read(uart, rx, 2, 5) != EP_OK) {
                    return 11;
                }

                if (rx[0] != 'A' || rx[1] != 'B') {
                    return 12;
                }

                fake_rt_set_read_data("C");
                if (ep_uart_read(uart, rx, 2, 0) != EP_ERR_TIMEOUT) {
                    return 13;
                }

                fake_rt_set_read_data("");
                fake_rt_reset_delay_count();
                if (ep_uart_read(uart, rx, 2, 3) != EP_ERR_TIMEOUT) {
                    return 20;
                }

                if (fake_rt_delay_count() != 3) {
                    return 21;
                }

                if (ep_uart_write(0, "OK", 2) != EP_ERR_INVAL) {
                    return 14;
                }

                if (ep_uart_read(0, rx, 2, 0) != EP_ERR_INVAL) {
                    return 15;
                }

                if (ep_uart_close(0) != EP_ERR_INVAL) {
                    return 16;
                }

                if (ep_uart_close(uart) != EP_OK) {
                    return 17;
                }

                if (ep_uart_open(&console, "console_uart") != EP_OK) {
                    return 18;
                }

                if (fake_rt_last_find_name()[0] != 'u' || fake_rt_last_find_name()[4] != '1') {
                    return 19;
                }

                (void)ep_uart_close(console);
                return 0;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_include = tmp_path / "rtthread.h"
    rtthread_include.write_text(
        textwrap.dedent(
            """
            #ifndef RTTHREAD_H
            #define RTTHREAD_H

            #include <stddef.h>
            #include <stdint.h>

            typedef int rt_err_t;
            typedef int rt_int32_t;
            typedef int rt_off_t;
            typedef size_t rt_size_t;
            typedef unsigned short rt_uint16_t;

            #define RT_EOK 0
            #define RT_ERROR 1
            #define RT_NULL ((void *)0)
            #define RT_DEVICE_OFLAG_RDWR 0x003
            #define RT_DEVICE_FLAG_INT_RX 0x100
            #define RT_DEVICE_FLAG_STREAM 0x040

            typedef struct fake_device *rt_device_t;

            rt_device_t rt_device_find(const char *name);
            rt_err_t rt_device_open(rt_device_t dev, rt_uint16_t oflag);
            rt_err_t rt_device_close(rt_device_t dev);
            rt_size_t rt_device_read(rt_device_t dev, rt_off_t pos, void *buffer, rt_size_t size);
            rt_size_t rt_device_write(rt_device_t dev, rt_off_t pos, const void *buffer, rt_size_t size);
            rt_err_t rt_thread_mdelay(rt_int32_t timeout_ms);
            void *rt_malloc(rt_size_t size);
            void rt_free(void *ptr);

            const char *fake_rt_last_find_name(void);
            rt_uint16_t fake_rt_last_open_flags(void);
            const char *fake_rt_last_write(void);
            void fake_rt_set_read_data(const char *text);
            void fake_rt_reset_delay_count(void);
            int fake_rt_delay_count(void);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_fake = tmp_path / "fake_rtthread.c"
    rtthread_fake.write_text(
        textwrap.dedent(
            """
            #include "rtthread.h"

            #include <stdlib.h>
            #include <string.h>

            struct fake_device {
                const char *name;
                int open;
            };

            static struct fake_device uart1 = {"uart1", 0};
            static struct fake_device uart2 = {"uart2", 0};
            static char last_find_name[32];
            static char last_write[32];
            static char read_data[32];
            static rt_size_t read_offset;
            static rt_uint16_t last_open_flags;
            static int delay_count;

            void *rt_malloc(rt_size_t size)
            {
                return malloc(size);
            }

            void rt_free(void *ptr)
            {
                free(ptr);
            }

            rt_err_t rt_thread_mdelay(rt_int32_t timeout_ms)
            {
                (void)timeout_ms;
                ++delay_count;
                return RT_EOK;
            }

            void fake_rt_reset_delay_count(void)
            {
                delay_count = 0;
            }

            int fake_rt_delay_count(void)
            {
                return delay_count;
            }

            const char *fake_rt_last_find_name(void)
            {
                return last_find_name;
            }

            rt_uint16_t fake_rt_last_open_flags(void)
            {
                return last_open_flags;
            }

            const char *fake_rt_last_write(void)
            {
                return last_write;
            }

            void fake_rt_set_read_data(const char *text)
            {
                (void)strncpy(read_data, text, sizeof(read_data) - 1u);
                read_data[sizeof(read_data) - 1u] = '\\0';
                read_offset = 0;
            }

            rt_device_t rt_device_find(const char *name)
            {
                (void)strncpy(last_find_name, name, sizeof(last_find_name) - 1u);
                last_find_name[sizeof(last_find_name) - 1u] = '\\0';

                if (strcmp(name, "uart1") == 0) {
                    return &uart1;
                }

                if (strcmp(name, "uart2") == 0) {
                    return &uart2;
                }

                return RT_NULL;
            }

            rt_err_t rt_device_open(rt_device_t dev, rt_uint16_t oflag)
            {
                if (dev == RT_NULL) {
                    return -RT_ERROR;
                }

                last_open_flags = oflag;
                dev->open = 1;
                return RT_EOK;
            }

            rt_err_t rt_device_close(rt_device_t dev)
            {
                if (dev == RT_NULL) {
                    return -RT_ERROR;
                }

                dev->open = 0;
                return RT_EOK;
            }

            rt_size_t rt_device_write(rt_device_t dev, rt_off_t pos, const void *buffer, rt_size_t size)
            {
                (void)pos;

                if (dev == RT_NULL || dev->open == 0 || size >= sizeof(last_write)) {
                    return 0;
                }

                (void)memcpy(last_write, buffer, size);
                last_write[size] = '\\0';
                return size;
            }

            rt_size_t rt_device_read(rt_device_t dev, rt_off_t pos, void *buffer, rt_size_t size)
            {
                rt_size_t available;
                char *out;

                (void)pos;

                if (dev == RT_NULL || dev->open == 0) {
                    return 0;
                }

                available = (rt_size_t)strlen(read_data + read_offset);
                if (available == 0u || size == 0u) {
                    return 0;
                }

                out = (char *)buffer;
                out[0] = read_data[read_offset];
                ++read_offset;
                return 1;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(tmp_path),
            "-I",
            str(REPO_ROOT / "hal" / "include"),
            "-I",
            str(REPO_ROOT / "osal" / "include"),
            str(source),
            str(rtthread_fake),
            str(REPO_ROOT / "platforms/rtos/demo_family/hal_port/ep_rtos_hal_rtthread.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, (
        f"compile failed\nstdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run_result.returncode == 0, (
        f"run failed\nstdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
