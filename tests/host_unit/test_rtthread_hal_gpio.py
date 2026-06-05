import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_rtthread_hal_gpio_maps_logical_names_to_rtthread_pins(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtthread_hal_gpio_smoke.c"
    executable = tmp_path / "rtthread_hal_gpio_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_hal_err.h"
            #include "ep_hal_gpio.h"
            #include "drivers/pin.h"
            #include "rtthread.h"

            #include <string.h>

            int main(void)
            {
                ep_gpio_t *gpio = 0;
                ep_gpio_t *panel = 0;
                int value = -1;

                if (ep_gpio_request(0, "lcd_sleep_gpio") == EP_OK) {
                    return 1;
                }

                gpio = (ep_gpio_t *)1;
                if (ep_gpio_request(&gpio, "missing_gpio") == EP_OK) {
                    return 2;
                }

                if (gpio != 0) {
                    return 3;
                }

                if (ep_gpio_request(&gpio, "lcd_sleep_gpio") != EP_OK) {
                    return 4;
                }

                if (strcmp(fake_pin_last_get_name(), "PD.3") != 0) {
                    return 5;
                }

                if (ep_gpio_request(&panel, "lcd_sleep_gpio") != EP_ERR_BUSY) {
                    return 19;
                }

                if (ep_gpio_set_direction(gpio, EP_GPIO_OUTPUT) != EP_OK) {
                    return 6;
                }

                if (fake_pin_last_mode() != PIN_MODE_OUTPUT) {
                    return 7;
                }

                if (ep_gpio_write(gpio, 1) != EP_OK) {
                    return 8;
                }

                if (fake_pin_last_write_value() != PIN_HIGH) {
                    return 9;
                }

                if (ep_gpio_read(gpio, &value) != EP_OK) {
                    return 10;
                }

                if (value != 1) {
                    return 11;
                }

                if (ep_gpio_set_direction(gpio, EP_GPIO_INPUT) != EP_OK) {
                    return 12;
                }

                if (fake_pin_last_mode() != PIN_MODE_INPUT) {
                    return 13;
                }

                if (ep_gpio_write(gpio, 0) != EP_ERR_INVAL) {
                    return 14;
                }

                if (ep_gpio_read(0, &value) != EP_ERR_INVAL) {
                    return 15;
                }

                if (ep_gpio_read(gpio, 0) != EP_ERR_INVAL) {
                    return 16;
                }

                panel = 0;
                if (ep_gpio_request(&panel, "panel_enable_gpio") != EP_OK) {
                    return 17;
                }

                if (strcmp(fake_pin_last_get_name(), "PE.13") != 0) {
                    return 18;
                }

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

            typedef int rt_base_t;
            typedef int rt_err_t;
            typedef size_t rt_size_t;

            #define RT_EOK 0
            #define RT_ERROR 1
            #define RT_NULL ((void *)0)

            void *rt_malloc(rt_size_t size);
            void rt_free(void *ptr);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    drivers_dir = tmp_path / "drivers"
    drivers_dir.mkdir()
    (drivers_dir / "pin.h").write_text(
        textwrap.dedent(
            """
            #ifndef PIN_H
            #define PIN_H

            #include "rtthread.h"

            #define PIN_LOW 0x00
            #define PIN_HIGH 0x01
            #define PIN_MODE_OUTPUT 0x00
            #define PIN_MODE_INPUT 0x01

            rt_base_t rt_pin_get(const char *name);
            void rt_pin_mode(rt_base_t pin, rt_base_t mode);
            void rt_pin_write(rt_base_t pin, rt_base_t value);
            int rt_pin_read(rt_base_t pin);

            const char *fake_pin_last_get_name(void);
            rt_base_t fake_pin_last_mode(void);
            rt_base_t fake_pin_last_write_value(void);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_fake = tmp_path / "fake_rtthread_pin.c"
    rtthread_fake.write_text(
        textwrap.dedent(
            """
            #include "drivers/pin.h"

            #include <stdlib.h>
            #include <string.h>

            static char last_get_name[32];
            static rt_base_t last_mode = -1;
            static rt_base_t last_write_value = -1;
            static int pin_value;

            void *rt_malloc(rt_size_t size)
            {
                return malloc(size);
            }

            void rt_free(void *ptr)
            {
                free(ptr);
            }

            const char *fake_pin_last_get_name(void)
            {
                return last_get_name;
            }

            rt_base_t fake_pin_last_mode(void)
            {
                return last_mode;
            }

            rt_base_t fake_pin_last_write_value(void)
            {
                return last_write_value;
            }

            rt_base_t rt_pin_get(const char *name)
            {
                (void)strncpy(last_get_name, name, sizeof(last_get_name) - 1u);
                last_get_name[sizeof(last_get_name) - 1u] = '\\0';

                if (strcmp(name, "PD.3") == 0) {
                    return 99;
                }

                if (strcmp(name, "PE.13") == 0) {
                    return 141;
                }

                return -1;
            }

            void rt_pin_mode(rt_base_t pin, rt_base_t mode)
            {
                (void)pin;
                last_mode = mode;
            }

            void rt_pin_write(rt_base_t pin, rt_base_t value)
            {
                (void)pin;
                last_write_value = value;
                pin_value = value == PIN_LOW ? 0 : 1;
            }

            int rt_pin_read(rt_base_t pin)
            {
                (void)pin;
                return pin_value;
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
            str(REPO_ROOT / "platforms/rtos/demo_family/hal_port/ep_rtos_hal_gpio_rtthread.c"),
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
