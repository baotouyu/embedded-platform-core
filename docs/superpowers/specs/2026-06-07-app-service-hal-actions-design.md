# App Service HAL Actions Design

## Overview

This design closes the first business-service-to-HAL loop for the application layer.

The goal is to keep product code in `app/` portable while letting selected business services perform real hardware actions on the ArtInChip RTOS target. Host and Linux builds must keep compiling so the same business code can still be edited and checked on macOS or Linux before switching to the target build.

## Scope

Implement the first three concrete service actions:

- `beep_service_beep_ms()`
- `rtc_service_get_time()`
- `lcd_sleep_service_set_sleep()`

Keep these services out of scope for this step:

- display and touch, because the platform LVGL path already owns them
- SPI and ADC, because the current product code does not use them yet
- SD card filesystem, because the vendor SDK already exposes file access through standard file APIs
- power-board UART protocol, because the protocol will be designed later

## Architecture

The dependency direction remains:

```text
app/services -> hal/include + osal/include -> platforms/*/hal_port
```

`app/services` may include portable HAL and OSAL headers, but it must not include RT-Thread, Linux, or vendor SDK headers.

The platform behavior is:

- ArtInChip RTOS: calls the real RT-Thread HAL ports under `platforms/rtos/demo_family/hal_port/`
- host POSIX: calls host HAL stubs so macOS development builds keep linking
- Linux demo: calls Linux HAL stubs until a real Linux board port is added

## Service Behavior

### Beep

`beep_service_beep_ms(duration_ms)` opens the logical PWM device `beep_pwm`.

Rules:

- `duration_ms == 0` returns `EP_ERR_INVAL`.
- Frequency is `BEEP_SERVICE_DEFAULT_FREQUENCY_HZ`, currently `2700`.
- PWM period is computed in nanoseconds from the configured frequency.
- Duty cycle is 50%.
- The service enables PWM, sleeps for `duration_ms`, disables PWM, then closes the handle.
- Disable and close are best-effort cleanup steps after a successful enable.

On KI-141103-480p this maps to `PWM1 PC7` through the RTOS HAL resource mapping.

### RTC

`rtc_service_get_time(time)` opens the logical RTC device `rtc`.

Rules:

- `time == NULL` returns `EP_ERR_INVAL`.
- The service calls `ep_rtc_get_time()`.
- The service closes the RTC handle after the read.
- If the read succeeds but close fails, the close error is returned.

On KI-141103-480p this maps to PCF8563 on `I2C1 PD4/PD5` through the RTOS HAL resource mapping.

### LCD Sleep

`lcd_sleep_service_init()` requests the logical GPIO device `lcd_sleep_gpio` once and configures it as output.

`lcd_sleep_service_set_sleep(sleep_enabled)` writes the sleep state:

- `sleep_enabled == 0` writes `0`
- `sleep_enabled != 0` writes `1`

The current hardware assumption is active-high sleep: high means sleep, low means wake.

On KI-141103-480p this maps to `PD3` through the RTOS HAL resource mapping.

## Host And Linux Stubs

The existing host and Linux HAL stub files must provide linkable implementations for the HAL APIs used by these services.

Stub behavior:

- invalid pointer arguments return `EP_ERR_INVAL`
- otherwise unsupported hardware actions return `EP_ERR_UNSUPPORTED`

This keeps macOS and Linux development builds usable without pretending that hardware exists on the host.

## Error Handling

Each service returns the first meaningful error from the lower layer.

The services do not hide HAL failures. This is intentional: board bring-up and business logic should see whether a device is missing, unsupported, or rejected invalid input.

## Testing

Tests are written before implementation.

Required coverage:

- Beep service validates zero duration.
- Beep service opens `beep_pwm`, sets a 2700 Hz 50% PWM waveform, enables it, sleeps, disables it, and closes it.
- RTC service rejects null output pointers.
- RTC service opens `rtc`, reads time, and closes the handle.
- LCD sleep service requests `lcd_sleep_gpio`, configures output, and writes `0` or `1`.
- Host and Linux demo builds still link after services call HAL APIs.

Target verification:

- CMake host build must pass.
- Python host and API-contract tests must pass.
- ArtInChip Docker firmware build for `artinchip_d12x_lubanlite_ki_141103_480p` must pass.
