# App Service HAL Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the first app business services call portable HAL APIs while keeping host, Linux, and ArtInChip RTOS builds linkable.

**Architecture:** `app/services` will call only `hal/include` and `osal/include` APIs. ArtInChip RTOS uses real HAL ports, while host POSIX and Linux demo provide unsupported-but-linkable HAL stubs.

**Tech Stack:** C services, C HAL/OSAL headers, CMake host builds, pytest compile-and-run host unit tests, Luban-Lite Docker firmware build.

---

### Task 1: Add Service Behavior Tests

**Files:**
- Create: `tests/host_unit/test_app_service_hal_actions.py`

- [ ] **Step 1: Write failing compile-and-run tests**

Create `tests/host_unit/test_app_service_hal_actions.py` with three tests:

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def _compile_and_run(tmp_path, name, main_source, repo_sources):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / f"{name}.c"
    executable = tmp_path / name
    source.write_text(textwrap.dedent(main_source).strip() + "\n", encoding="utf-8")

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c99",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(REPO_ROOT / "app/services"),
            "-I",
            str(REPO_ROOT / "hal/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            "-I",
            str(REPO_ROOT / "components/log/include"),
            str(source),
            *[str(REPO_ROOT / repo_source) for repo_source in repo_sources],
            "-o",
            str(executable),
        ],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(executable)],
        cwd=tmp_path,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert run_result.returncode == 0, run_result.stdout + run_result.stderr


def test_beep_service_uses_beep_pwm_at_2700hz(tmp_path):
    _compile_and_run(
        tmp_path,
        "beep_service_action_smoke",
        """
        #include "beep_service.h"
        #include "ep_hal_err.h"
        #include "ep_hal_pwm.h"
        #include "ep_log.h"
        #include "ep_osal_time.h"

        #include <stdarg.h>
        #include <string.h>

        struct ep_pwm {
            int marker;
        };

        static struct ep_pwm fake_pwm;
        static char opened_name[32];
        static unsigned int last_period_ns;
        static unsigned int last_duty_ns;
        static unsigned int slept_ms;
        static int open_count;
        static int enable_count;
        static int disable_count;
        static int close_count;

        int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...)
        {
            (void)level;
            (void)tag;
            (void)fmt;
            return EP_OK;
        }

        uint64_t ep_time_now_ms(void)
        {
            return 0u;
        }

        void ep_sleep_ms(unsigned int timeout_ms)
        {
            slept_ms = timeout_ms;
        }

        int ep_pwm_open(ep_pwm_t **pwm, const char *name)
        {
            if (pwm == 0 || name == 0) {
                return EP_ERR_INVAL;
            }

            (void)strncpy(opened_name, name, sizeof(opened_name) - 1u);
            opened_name[sizeof(opened_name) - 1u] = '\\0';
            *pwm = &fake_pwm;
            open_count++;
            return EP_OK;
        }

        int ep_pwm_set(ep_pwm_t *pwm, unsigned int period_ns, unsigned int duty_ns)
        {
            if (pwm == 0) {
                return EP_ERR_INVAL;
            }

            last_period_ns = period_ns;
            last_duty_ns = duty_ns;
            return EP_OK;
        }

        int ep_pwm_enable(ep_pwm_t *pwm)
        {
            if (pwm == 0) {
                return EP_ERR_INVAL;
            }

            enable_count++;
            return EP_OK;
        }

        int ep_pwm_disable(ep_pwm_t *pwm)
        {
            if (pwm == 0) {
                return EP_ERR_INVAL;
            }

            disable_count++;
            return EP_OK;
        }

        int ep_pwm_close(ep_pwm_t *pwm)
        {
            if (pwm == 0) {
                return EP_ERR_INVAL;
            }

            close_count++;
            return EP_OK;
        }

        int main(void)
        {
            if (beep_service_beep_ms(0u) != EP_ERR_INVAL) {
                return 1;
            }

            if (beep_service_beep_ms(120u) != EP_OK) {
                return 2;
            }

            if (strcmp(opened_name, "beep_pwm") != 0) {
                return 3;
            }

            if (last_period_ns != 370370u || last_duty_ns != 185185u) {
                return 4;
            }

            if (slept_ms != 120u) {
                return 5;
            }

            if (open_count != 1 || enable_count != 1 ||
                disable_count != 1 || close_count != 1) {
                return 6;
            }

            return 0;
        }
        """,
        ["app/services/beep_service.c"],
    )


def test_rtc_service_reads_time_and_closes_handle(tmp_path):
    _compile_and_run(
        tmp_path,
        "rtc_service_action_smoke",
        """
        #include "rtc_service.h"
        #include "ep_hal_err.h"
        #include "ep_hal_rtc.h"
        #include "ep_log.h"

        #include <stdarg.h>
        #include <string.h>

        struct ep_rtc {
            int marker;
        };

        static struct ep_rtc fake_rtc;
        static char opened_name[32];
        static int get_count;
        static int close_count;

        int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...)
        {
            (void)level;
            (void)tag;
            (void)fmt;
            return EP_OK;
        }

        int ep_rtc_open(ep_rtc_t **rtc, const char *name)
        {
            if (rtc == 0 || name == 0) {
                return EP_ERR_INVAL;
            }

            (void)strncpy(opened_name, name, sizeof(opened_name) - 1u);
            opened_name[sizeof(opened_name) - 1u] = '\\0';
            *rtc = &fake_rtc;
            return EP_OK;
        }

        int ep_rtc_get_time(ep_rtc_t *rtc, ep_rtc_time_t *time)
        {
            if (rtc == 0 || time == 0) {
                return EP_ERR_INVAL;
            }

            time->year = 2026u;
            time->month = 6u;
            time->day = 7u;
            time->hour = 10u;
            time->minute = 11u;
            time->second = 12u;
            time->weekday = 0u;
            get_count++;
            return EP_OK;
        }

        int ep_rtc_set_time(ep_rtc_t *rtc, const ep_rtc_time_t *time)
        {
            (void)rtc;
            (void)time;
            return EP_ERR_UNSUPPORTED;
        }

        int ep_rtc_close(ep_rtc_t *rtc)
        {
            if (rtc == 0) {
                return EP_ERR_INVAL;
            }

            close_count++;
            return EP_OK;
        }

        int main(void)
        {
            ep_rtc_time_t time = {0};

            if (rtc_service_get_time(0) != EP_ERR_INVAL) {
                return 1;
            }

            if (rtc_service_get_time(&time) != EP_OK) {
                return 2;
            }

            if (strcmp(opened_name, "rtc") != 0) {
                return 3;
            }

            if (time.year != 2026u || time.month != 6u || time.day != 7u ||
                time.hour != 10u || time.minute != 11u || time.second != 12u ||
                time.weekday != 0u) {
                return 4;
            }

            if (get_count != 1 || close_count != 1) {
                return 5;
            }

            return 0;
        }
        """,
        ["app/services/rtc_service.c"],
    )


def test_lcd_sleep_service_requests_gpio_once_and_writes_state(tmp_path):
    _compile_and_run(
        tmp_path,
        "lcd_sleep_service_action_smoke",
        """
        #include "lcd_sleep_service.h"
        #include "ep_hal_err.h"
        #include "ep_hal_gpio.h"
        #include "ep_log.h"

        #include <stdarg.h>
        #include <string.h>

        struct ep_gpio {
            int marker;
        };

        static struct ep_gpio fake_gpio;
        static char requested_name[32];
        static ep_gpio_dir_e last_direction;
        static int request_count;
        static int direction_count;
        static int last_write_value = -1;

        int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...)
        {
            (void)level;
            (void)tag;
            (void)fmt;
            return EP_OK;
        }

        int ep_gpio_request(ep_gpio_t **gpio, const char *name)
        {
            if (gpio == 0 || name == 0) {
                return EP_ERR_INVAL;
            }

            (void)strncpy(requested_name, name, sizeof(requested_name) - 1u);
            requested_name[sizeof(requested_name) - 1u] = '\\0';
            *gpio = &fake_gpio;
            request_count++;
            return EP_OK;
        }

        int ep_gpio_set_direction(ep_gpio_t *gpio, ep_gpio_dir_e dir)
        {
            if (gpio == 0) {
                return EP_ERR_INVAL;
            }

            last_direction = dir;
            direction_count++;
            return EP_OK;
        }

        int ep_gpio_write(ep_gpio_t *gpio, int value)
        {
            if (gpio == 0) {
                return EP_ERR_INVAL;
            }

            last_write_value = value;
            return EP_OK;
        }

        int ep_gpio_read(ep_gpio_t *gpio, int *value)
        {
            (void)gpio;
            (void)value;
            return EP_ERR_UNSUPPORTED;
        }

        int main(void)
        {
            if (lcd_sleep_service_init() != EP_OK) {
                return 1;
            }

            if (strcmp(requested_name, "lcd_sleep_gpio") != 0) {
                return 2;
            }

            if (last_direction != EP_GPIO_OUTPUT) {
                return 3;
            }

            if (lcd_sleep_service_set_sleep(0) != EP_OK || last_write_value != 0) {
                return 4;
            }

            if (lcd_sleep_service_set_sleep(9) != EP_OK || last_write_value != 1) {
                return 5;
            }

            if (request_count != 1 || direction_count != 1) {
                return 6;
            }

            return 0;
        }
        """,
        ["app/services/lcd_sleep_service.c"],
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest tests/host_unit/test_app_service_hal_actions.py -q
```

Expected: all three tests fail because current service actions return `EP_ERR_UNSUPPORTED`.

### Task 2: Implement Service HAL Calls

**Files:**
- Modify: `app/services/beep_service.c`
- Modify: `app/services/rtc_service.c`
- Modify: `app/services/lcd_sleep_service.c`

- [ ] **Step 1: Implement minimal service behavior**

`beep_service.c` must include `ep_hal_pwm.h` and `ep_osal_time.h`, validate zero duration, open `beep_pwm`, set period `1000000000u / BEEP_SERVICE_DEFAULT_FREQUENCY_HZ`, duty `period / 2u`, enable, sleep, disable, and close.

`rtc_service.c` must include `ep_hal_rtc.h`, validate null time pointers, open `rtc`, read time, and close.

`lcd_sleep_service.c` must include `ep_hal_gpio.h`, keep a static `ep_gpio_t *`, request `lcd_sleep_gpio` once during init, set output direction once, and write `sleep_enabled ? 1 : 0`.

- [ ] **Step 2: Run service tests**

Run:

```bash
python3 -m pytest tests/host_unit/test_app_service_hal_actions.py -q
```

Expected: `3 passed`.

### Task 3: Add Host And Linux HAL Stubs

**Files:**
- Modify: `platforms/host/posix/hal_port/ep_host_hal_stub.c`
- Modify: `platforms/linux/demo_family/hal_port/ep_linux_hal_stub.c`

- [ ] **Step 1: Add linkable GPIO/PWM/RTC stubs**

Both stub files must include the portable HAL headers and implement:

- `ep_pwm_open`, `ep_pwm_set`, `ep_pwm_enable`, `ep_pwm_disable`, `ep_pwm_close`
- `ep_gpio_request`, `ep_gpio_set_direction`, `ep_gpio_write`, `ep_gpio_read`
- `ep_rtc_open`, `ep_rtc_get_time`, `ep_rtc_set_time`, `ep_rtc_close`

Invalid pointer inputs return `EP_ERR_INVAL`; supported signatures with unavailable hardware return `EP_ERR_UNSUPPORTED`.

- [ ] **Step 2: Build host and Linux demo targets**

Run:

```bash
cmake -S . -B build
cmake --build build --target ep_platform_host_posix ep_platform_linux_demo
```

Expected: both targets build successfully.

### Task 4: Docs And Verification

**Files:**
- Modify: `docs/porting/app-business-skeleton.md`
- Modify: `docs/porting/hal-api-reference.md`

- [ ] **Step 1: Update docs**

Document that:

- business services now call portable HAL APIs
- host/Linux HAL stubs keep non-target builds linkable and return unsupported
- AIC RTOS maps `beep_pwm`, `lcd_sleep_gpio`, and `rtc` to board resources

- [ ] **Step 2: Run verification**

Run:

```bash
python3 -m pytest tests/host_unit/test_app_service_hal_actions.py tests/host_unit tests/api_contract -q
./build.sh validate-targets
cmake --build build --target ep_platform_host_posix ep_platform_linux_demo ep_app_core_export
docker exec -u yuwei -w /home/yuwei/samba/yuwei_work/project/embedded-platform-core ubuntu20.04-build bash -lc './build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p --clean'
```

Expected: tests pass, target validation passes, host/Linux/export builds pass, and the AIC firmware image is generated under `out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/`.

- [ ] **Step 3: Commit implementation**

Run:

```bash
git add app/services platforms/host/posix/hal_port/ep_host_hal_stub.c platforms/linux/demo_family/hal_port/ep_linux_hal_stub.c tests/host_unit/test_app_service_hal_actions.py docs/porting/app-business-skeleton.md docs/porting/hal-api-reference.md
git commit -m "feat: 接通应用服务层硬件动作"
```
