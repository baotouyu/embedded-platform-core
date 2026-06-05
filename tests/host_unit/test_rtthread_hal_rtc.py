import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_rtthread_hal_rtc_maps_rtc_to_pcf8563_on_i2c1(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtthread_hal_rtc_smoke.c"
    executable = tmp_path / "rtthread_hal_rtc_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_hal_err.h"
            #include "ep_hal_rtc.h"
            #include "drivers/i2c.h"
            #include "rtthread.h"

            #include <string.h>

            int main(void)
            {
                ep_rtc_t *rtc = 0;
                ep_rtc_t *raw_rtc = 0;
                ep_rtc_time_t time = {0};
                ep_rtc_time_t invalid = {0};

                if (ep_rtc_open(0, "rtc") == EP_OK) {
                    return 1;
                }

                rtc = (ep_rtc_t *)1;
                if (ep_rtc_open(&rtc, "missing_rtc") == EP_OK) {
                    return 2;
                }

                if (rtc != 0) {
                    return 3;
                }

                if (ep_rtc_open(&rtc, "rtc") != EP_OK) {
                    return 4;
                }

                if (strcmp(fake_i2c_last_find_name(), "i2c1") != 0) {
                    return 5;
                }

                if (ep_rtc_get_time(0, &time) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_rtc_get_time(rtc, 0) != EP_ERR_INVAL) {
                    return 7;
                }

                fake_pcf8563_set_time_regs(0x45, 0x30, 0x15, 0x05, 0x05, 0x06, 0x26);
                if (ep_rtc_get_time(rtc, &time) != EP_OK) {
                    return 8;
                }

                if (fake_i2c_transfer_count() != 2) {
                    return 9;
                }

                if (fake_i2c_msg_count_at(0) != 1 || fake_i2c_msg_count_at(1) != 1) {
                    return 10;
                }

                if (fake_i2c_flags_at(0) != RT_I2C_WR || fake_i2c_flags_at(1) != RT_I2C_RD) {
                    return 11;
                }

                if (fake_i2c_addr_at(0) != 0x51 || fake_i2c_addr_at(1) != 0x51) {
                    return 12;
                }

                if (fake_i2c_first_byte_at(0) != 0x02) {
                    return 13;
                }

                if (time.year != 2026 || time.month != 6 || time.day != 5 ||
                    time.weekday != 5 || time.hour != 15 ||
                    time.minute != 30 || time.second != 45) {
                    return 14;
                }

                fake_pcf8563_set_time_regs(0x80, 0x30, 0x15, 0x05, 0x05, 0x06, 0x26);
                if (ep_rtc_get_time(rtc, &time) != EP_ERR_UNSUPPORTED) {
                    return 15;
                }

                time.year = 2026;
                time.month = 6;
                time.day = 5;
                time.weekday = 5;
                time.hour = 15;
                time.minute = 30;
                time.second = 45;
                if (ep_rtc_set_time(rtc, &time) != EP_OK) {
                    return 16;
                }

                if (fake_i2c_last_write_len() != 8) {
                    return 17;
                }

                if (fake_i2c_last_write_byte(0) != 0x02 ||
                    fake_i2c_last_write_byte(1) != 0x45 ||
                    fake_i2c_last_write_byte(2) != 0x30 ||
                    fake_i2c_last_write_byte(3) != 0x15 ||
                    fake_i2c_last_write_byte(4) != 0x05 ||
                    fake_i2c_last_write_byte(5) != 0x05 ||
                    fake_i2c_last_write_byte(6) != 0x06 ||
                    fake_i2c_last_write_byte(7) != 0x26) {
                    return 18;
                }

                invalid = time;
                invalid.month = 13;
                if (ep_rtc_set_time(rtc, &invalid) != EP_ERR_INVAL) {
                    return 19;
                }

                invalid = time;
                invalid.day = 0;
                if (ep_rtc_set_time(rtc, &invalid) != EP_ERR_INVAL) {
                    return 20;
                }

                invalid = time;
                invalid.hour = 24;
                if (ep_rtc_set_time(rtc, &invalid) != EP_ERR_INVAL) {
                    return 21;
                }

                invalid = time;
                invalid.minute = 60;
                if (ep_rtc_set_time(rtc, &invalid) != EP_ERR_INVAL) {
                    return 22;
                }

                invalid = time;
                invalid.second = 60;
                if (ep_rtc_set_time(rtc, &invalid) != EP_ERR_INVAL) {
                    return 23;
                }

                invalid = time;
                invalid.weekday = 7;
                if (ep_rtc_set_time(rtc, &invalid) != EP_ERR_INVAL) {
                    return 24;
                }

                invalid = time;
                invalid.year = 2099;
                if (ep_rtc_set_time(rtc, &invalid) != EP_OK) {
                    return 25;
                }

                invalid = time;
                invalid.year = 2100;
                if (ep_rtc_set_time(rtc, &invalid) != EP_ERR_INVAL) {
                    return 26;
                }

                if (ep_rtc_close(0) != EP_ERR_INVAL) {
                    return 27;
                }

                if (ep_rtc_close(rtc) != EP_OK) {
                    return 28;
                }

                if (ep_rtc_open(&raw_rtc, "pcf8563") != EP_OK) {
                    return 29;
                }

                if (ep_rtc_close(raw_rtc) != EP_OK) {
                    return 30;
                }

                fake_i2c_set_transfer_result(0);
                if (ep_rtc_open(&rtc, "rtc") != EP_OK) {
                    return 31;
                }

                if (ep_rtc_get_time(rtc, &time) != EP_ERR_UNSUPPORTED) {
                    return 32;
                }

                fake_i2c_set_transfer_result(1);
                if (ep_rtc_close(rtc) != EP_OK) {
                    return 33;
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
            int fake_i2c_transfer_count(void);
            int fake_i2c_msg_count_at(int index);
            int fake_i2c_addr_at(int index);
            int fake_i2c_flags_at(int index);
            int fake_i2c_first_byte_at(int index);
            int fake_i2c_last_write_len(void);
            int fake_i2c_last_write_byte(int index);
            void fake_i2c_set_transfer_result(rt_size_t result);
            void fake_pcf8563_set_time_regs(rt_uint8_t second, rt_uint8_t minute,
                                            rt_uint8_t hour, rt_uint8_t day,
                                            rt_uint8_t weekday, rt_uint8_t month,
                                            rt_uint8_t year);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_fake = tmp_path / "fake_rtthread_rtc_i2c.c"
    rtthread_fake.write_text(
        textwrap.dedent(
            """
            #include "drivers/i2c.h"

            #include <stdlib.h>
            #include <string.h>

            static struct rt_i2c_bus_device i2c1 = {1};
            static char last_find_name[32];
            static rt_uint8_t pcf8563_regs[7] = {0x45, 0x30, 0x15, 0x05, 0x05, 0x06, 0x26};
            static rt_uint8_t selected_reg;
            static rt_uint8_t last_write[16];
            static int last_write_len;
            static int transfer_count;
            static int msg_count_log[8];
            static int addr_log[8];
            static int flags_log[8];
            static int first_byte_log[8];
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

            int fake_i2c_transfer_count(void)
            {
                return transfer_count;
            }

            int fake_i2c_msg_count_at(int index)
            {
                return msg_count_log[index];
            }

            int fake_i2c_addr_at(int index)
            {
                return addr_log[index];
            }

            int fake_i2c_flags_at(int index)
            {
                return flags_log[index];
            }

            int fake_i2c_first_byte_at(int index)
            {
                return first_byte_log[index];
            }

            int fake_i2c_last_write_len(void)
            {
                return last_write_len;
            }

            int fake_i2c_last_write_byte(int index)
            {
                return last_write[index];
            }

            void fake_i2c_set_transfer_result(rt_size_t result)
            {
                transfer_result = result;
            }

            void fake_pcf8563_set_time_regs(rt_uint8_t second, rt_uint8_t minute,
                                            rt_uint8_t hour, rt_uint8_t day,
                                            rt_uint8_t weekday, rt_uint8_t month,
                                            rt_uint8_t year)
            {
                pcf8563_regs[0] = second;
                pcf8563_regs[1] = minute;
                pcf8563_regs[2] = hour;
                pcf8563_regs[3] = day;
                pcf8563_regs[4] = weekday;
                pcf8563_regs[5] = month;
                pcf8563_regs[6] = year;
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
                rt_uint32_t i;
                int log_index = transfer_count;

                (void)bus;
                msg_count_log[log_index] = (int)num;
                addr_log[log_index] = msgs[0].addr;
                flags_log[log_index] = msgs[0].flags;
                first_byte_log[log_index] = msgs[0].buf != 0 && msgs[0].len > 0 ? msgs[0].buf[0] : -1;
                ++transfer_count;

                if (transfer_result != num) {
                    return transfer_result;
                }

                if ((msgs[0].flags & RT_I2C_RD) != 0u) {
                    for (i = 0; i < msgs[0].len && i < sizeof(pcf8563_regs); ++i) {
                        msgs[0].buf[i] = pcf8563_regs[selected_reg - 0x02u + i];
                    }
                    return num;
                }

                if (msgs[0].len > 0 && msgs[0].buf != 0) {
                    selected_reg = msgs[0].buf[0];
                    last_write_len = msgs[0].len;
                    for (i = 0; i < msgs[0].len && i < sizeof(last_write); ++i) {
                        last_write[i] = msgs[0].buf[i];
                    }
                }

                if (msgs[0].len == 8 && msgs[0].buf[0] == 0x02u) {
                    for (i = 0; i < 7u; ++i) {
                        pcf8563_regs[i] = msgs[0].buf[i + 1u];
                    }
                }

                return num;
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
            str(REPO_ROOT / "platforms/rtos/demo_family/hal_port/ep_rtos_hal_rtc_pcf8563.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert compile_result.returncode == 0, (
        f"compile failed\nstdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run_result.returncode == 0, (
        f"run failed with {run_result.returncode}\nstdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
