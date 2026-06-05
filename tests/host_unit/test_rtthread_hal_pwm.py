import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_rtthread_hal_pwm_maps_beep_pwm_to_pwm_channel_one(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtthread_hal_pwm_smoke.c"
    executable = tmp_path / "rtthread_hal_pwm_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_hal_err.h"
            #include "ep_hal_pwm.h"
            #include "rtthread.h"

            #include <string.h>

            int main(void)
            {
                ep_pwm_t *pwm = 0;

                if (ep_pwm_open(0, "beep_pwm") == EP_OK) {
                    return 1;
                }

                pwm = (ep_pwm_t *)1;
                if (ep_pwm_open(&pwm, "missing_pwm") == EP_OK) {
                    return 2;
                }

                if (pwm != 0) {
                    return 3;
                }

                if (ep_pwm_open(&pwm, "beep_pwm") != EP_OK) {
                    return 4;
                }

                if (strcmp(fake_rt_last_find_name(), "pwm") != 0) {
                    return 5;
                }

                if (ep_pwm_set(pwm, 0u, 0u) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_pwm_set(pwm, 370370u, 370371u) != EP_ERR_INVAL) {
                    return 7;
                }

                if (ep_pwm_set(pwm, 370370u, 185185u) != EP_OK) {
                    return 8;
                }

                if (fake_pwm_last_channel() != 1) {
                    return 9;
                }

                if (fake_pwm_last_period() != 370370u || fake_pwm_last_pulse() != 185185u) {
                    return 10;
                }

                if (ep_pwm_enable(pwm) != EP_OK) {
                    return 11;
                }

                if (fake_pwm_last_enabled_channel() != 1) {
                    return 12;
                }

                if (ep_pwm_disable(pwm) != EP_OK) {
                    return 13;
                }

                if (fake_pwm_last_disabled_channel() != 1) {
                    return 14;
                }

                if (ep_pwm_close(0) != EP_ERR_INVAL) {
                    return 15;
                }

                if (ep_pwm_close(pwm) != EP_OK) {
                    return 16;
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
            typedef uint32_t rt_uint32_t;

            #define RT_EOK 0
            #define RT_ERROR 1
            #define RT_NULL ((void *)0)

            struct rt_device {
                const char *name;
            };

            typedef struct rt_device *rt_device_t;

            rt_device_t rt_device_find(const char *name);
            void *rt_malloc(rt_size_t size);
            void rt_free(void *ptr);

            const char *fake_rt_last_find_name(void);
            int fake_pwm_last_channel(void);
            rt_uint32_t fake_pwm_last_period(void);
            rt_uint32_t fake_pwm_last_pulse(void);
            int fake_pwm_last_enabled_channel(void);
            int fake_pwm_last_disabled_channel(void);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    drivers_dir = tmp_path / "drivers"
    drivers_dir.mkdir()
    (drivers_dir / "rt_drv_pwm.h").write_text(
        textwrap.dedent(
            """
            #ifndef RT_DRV_PWM_H
            #define RT_DRV_PWM_H

            #include "rtthread.h"

            struct rt_device_pwm {
                struct rt_device parent;
            };

            rt_err_t rt_pwm_set(struct rt_device_pwm *device, int channel,
                                rt_uint32_t period, rt_uint32_t pulse);
            rt_err_t rt_pwm_enable(struct rt_device_pwm *device, int channel);
            rt_err_t rt_pwm_disable(struct rt_device_pwm *device, int channel);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_fake = tmp_path / "fake_rtthread_pwm.c"
    rtthread_fake.write_text(
        textwrap.dedent(
            """
            #include "drivers/rt_drv_pwm.h"

            #include <stdlib.h>
            #include <string.h>

            static struct rt_device_pwm pwm_dev = {{"pwm"}};
            static char last_find_name[32];
            static int last_channel;
            static int last_enabled_channel;
            static int last_disabled_channel;
            static rt_uint32_t last_period;
            static rt_uint32_t last_pulse;

            void *rt_malloc(rt_size_t size)
            {
                return malloc(size);
            }

            void rt_free(void *ptr)
            {
                free(ptr);
            }

            const char *fake_rt_last_find_name(void)
            {
                return last_find_name;
            }

            int fake_pwm_last_channel(void)
            {
                return last_channel;
            }

            rt_uint32_t fake_pwm_last_period(void)
            {
                return last_period;
            }

            rt_uint32_t fake_pwm_last_pulse(void)
            {
                return last_pulse;
            }

            int fake_pwm_last_enabled_channel(void)
            {
                return last_enabled_channel;
            }

            int fake_pwm_last_disabled_channel(void)
            {
                return last_disabled_channel;
            }

            rt_device_t rt_device_find(const char *name)
            {
                (void)strncpy(last_find_name, name, sizeof(last_find_name) - 1u);
                last_find_name[sizeof(last_find_name) - 1u] = '\\0';

                if (strcmp(name, "pwm") == 0) {
                    return &pwm_dev.parent;
                }

                return RT_NULL;
            }

            rt_err_t rt_pwm_set(struct rt_device_pwm *device, int channel,
                                rt_uint32_t period, rt_uint32_t pulse)
            {
                if (device == RT_NULL) {
                    return -RT_ERROR;
                }

                last_channel = channel;
                last_period = period;
                last_pulse = pulse;
                return RT_EOK;
            }

            rt_err_t rt_pwm_enable(struct rt_device_pwm *device, int channel)
            {
                if (device == RT_NULL) {
                    return -RT_ERROR;
                }

                last_enabled_channel = channel;
                return RT_EOK;
            }

            rt_err_t rt_pwm_disable(struct rt_device_pwm *device, int channel)
            {
                if (device == RT_NULL) {
                    return -RT_ERROR;
                }

                last_disabled_channel = channel;
                return RT_EOK;
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
            str(REPO_ROOT / "platforms/rtos/demo_family/hal_port/ep_rtos_hal_pwm_rtthread.c"),
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
