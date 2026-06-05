import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_rtthread_hal_i2c_maps_rtc_bus_to_i2c1(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtthread_hal_i2c_smoke.c"
    executable = tmp_path / "rtthread_hal_i2c_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_hal_err.h"
            #include "ep_hal_i2c.h"
            #include "drivers/i2c.h"
            #include "rtthread.h"

            #include <string.h>

            int main(void)
            {
                ep_i2c_t *bus = 0;
                ep_i2c_t *raw_bus = 0;
                unsigned char tx[2] = {0x12, 0x34};
                unsigned char rx[3] = {0};

                if (ep_i2c_open(0, "rtc_bus") == EP_OK) {
                    return 1;
                }

                bus = (ep_i2c_t *)1;
                if (ep_i2c_open(&bus, "missing_bus") == EP_OK) {
                    return 2;
                }

                if (bus != 0) {
                    return 3;
                }

                if (ep_i2c_open(&bus, "rtc_bus") != EP_OK) {
                    return 4;
                }

                if (strcmp(fake_i2c_last_find_name(), "i2c1") != 0) {
                    return 5;
                }

                if (ep_i2c_write(bus, 0x51, tx, sizeof(tx)) != EP_OK) {
                    return 6;
                }

                if (fake_i2c_last_transfer_msg_count() != 1) {
                    return 7;
                }

                if (fake_i2c_last_addr() != 0x51) {
                    return 8;
                }

                if (fake_i2c_last_flags() != RT_I2C_WR) {
                    return 9;
                }

                if (fake_i2c_last_len() != sizeof(tx)) {
                    return 10;
                }

                if (fake_i2c_last_buf0() != 0x12) {
                    return 11;
                }

                if (ep_i2c_read(bus, 0x51, rx, sizeof(rx)) != EP_OK) {
                    return 12;
                }

                if (fake_i2c_last_transfer_msg_count() != 1) {
                    return 13;
                }

                if (fake_i2c_last_addr() != 0x51) {
                    return 14;
                }

                if (fake_i2c_last_flags() != RT_I2C_RD) {
                    return 15;
                }

                if (fake_i2c_last_len() != sizeof(rx)) {
                    return 16;
                }

                if (rx[0] != 0xa5 || rx[1] != 0xa6 || rx[2] != 0xa7) {
                    return 17;
                }

                if (ep_i2c_write(bus, 0x51, tx, 0) != EP_OK) {
                    return 18;
                }

                if (ep_i2c_write(0, 0x51, tx, sizeof(tx)) != EP_ERR_INVAL) {
                    return 19;
                }

                if (ep_i2c_write(bus, 0x51, 0, sizeof(tx)) != EP_ERR_INVAL) {
                    return 20;
                }

                if (ep_i2c_read(bus, 0x51, 0, sizeof(rx)) != EP_ERR_INVAL) {
                    return 21;
                }

                fake_i2c_set_transfer_result(0);
                if (ep_i2c_read(bus, 0x51, rx, sizeof(rx)) != EP_ERR_UNSUPPORTED) {
                    return 22;
                }
                fake_i2c_set_transfer_result(1);

                if (ep_i2c_open(&raw_bus, "i2c1") != EP_OK) {
                    return 23;
                }

                if (strcmp(fake_i2c_last_find_name(), "i2c1") != 0) {
                    return 24;
                }

                if (raw_bus != bus) {
                    return 25;
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

            typedef int rt_err_t;
            typedef size_t rt_size_t;
            typedef uint8_t rt_uint8_t;
            typedef uint16_t rt_uint16_t;
            typedef uint32_t rt_uint32_t;

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
    (drivers_dir / "i2c.h").write_text(
        textwrap.dedent(
            """
            #ifndef DRIVERS_I2C_H
            #define DRIVERS_I2C_H

            #include "rtthread.h"

            #define RT_I2C_WR 0x0000
            #define RT_I2C_RD (1u << 0)

            struct rt_i2c_msg
            {
                rt_uint16_t addr;
                rt_uint16_t flags;
                rt_uint16_t len;
                rt_uint8_t *buf;
            };

            struct rt_i2c_bus_device
            {
                int marker;
            };

            struct rt_i2c_bus_device *rt_i2c_bus_device_find(const char *bus_name);
            rt_size_t rt_i2c_transfer(struct rt_i2c_bus_device *bus,
                                      struct rt_i2c_msg msgs[],
                                      rt_uint32_t num);

            const char *fake_i2c_last_find_name(void);
            int fake_i2c_last_transfer_msg_count(void);
            int fake_i2c_last_addr(void);
            int fake_i2c_last_flags(void);
            int fake_i2c_last_len(void);
            int fake_i2c_last_buf0(void);
            void fake_i2c_set_transfer_result(rt_size_t result);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_fake = tmp_path / "fake_rtthread_i2c.c"
    rtthread_fake.write_text(
        textwrap.dedent(
            """
            #include "drivers/i2c.h"

            #include <stdlib.h>
            #include <string.h>

            static struct rt_i2c_bus_device i2c1 = {1};
            static char last_find_name[32];
            static int last_transfer_msg_count;
            static int last_addr = -1;
            static int last_flags = -1;
            static int last_len = -1;
            static int last_buf0 = -1;
            static rt_size_t transfer_result = 1;

            void *rt_malloc(rt_size_t size)
            {
                return malloc(size);
            }

            void rt_free(void *ptr)
            {
                free(ptr);
            }

            const char *fake_i2c_last_find_name(void)
            {
                return last_find_name;
            }

            int fake_i2c_last_transfer_msg_count(void)
            {
                return last_transfer_msg_count;
            }

            int fake_i2c_last_addr(void)
            {
                return last_addr;
            }

            int fake_i2c_last_flags(void)
            {
                return last_flags;
            }

            int fake_i2c_last_len(void)
            {
                return last_len;
            }

            int fake_i2c_last_buf0(void)
            {
                return last_buf0;
            }

            void fake_i2c_set_transfer_result(rt_size_t result)
            {
                transfer_result = result;
            }

            struct rt_i2c_bus_device *rt_i2c_bus_device_find(const char *bus_name)
            {
                (void)strncpy(last_find_name, bus_name, sizeof(last_find_name) - 1u);
                last_find_name[sizeof(last_find_name) - 1u] = '\\0';

                if (strcmp(bus_name, "i2c1") == 0) {
                    return &i2c1;
                }

                return 0;
            }

            rt_size_t rt_i2c_transfer(struct rt_i2c_bus_device *bus,
                                      struct rt_i2c_msg msgs[],
                                      rt_uint32_t num)
            {
                unsigned int i;

                (void)bus;
                last_transfer_msg_count = (int)num;
                last_addr = msgs[0].addr;
                last_flags = msgs[0].flags;
                last_len = msgs[0].len;
                last_buf0 = msgs[0].buf != 0 && msgs[0].len > 0 ? msgs[0].buf[0] : -1;

                if ((msgs[0].flags & RT_I2C_RD) != 0u && msgs[0].buf != 0) {
                    for (i = 0; i < msgs[0].len; ++i) {
                        msgs[0].buf[i] = (rt_uint8_t)(0xa5u + i);
                    }
                }

                return transfer_result == num ? num : transfer_result;
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
            str(REPO_ROOT / "platforms/rtos/demo_family/hal_port/ep_rtos_hal_i2c_rtthread.c"),
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
