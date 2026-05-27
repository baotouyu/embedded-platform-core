# Embedded Platform Core Design

## Overview

This document defines the baseline architecture for a portable embedded platform framework that supports RTOS and Linux user space with a unified application-facing API.

The framework keeps RTOS vendor SDKs intact, wraps them with a platform adaptation layer, and exposes stable OS, driver, and component abstractions to upper layers. Linux does not use a vendor SDK layer; it maps the same abstractions onto standard Linux user-space interfaces.

The first-phase objective is to let one application codebase run on RTOS and Linux with no application-layer source changes, except for platform selection and build configuration.

## Goals

- Support RTOS and Linux user space under one framework architecture.
- Preserve RTOS vendor SDK startup and driver models instead of replacing them.
- Provide unified OS, driver, and common-component abstractions.
- Keep application code independent from platform headers and platform-specific control flow.
- Allow more platforms, chip families, and boards to be added without restructuring the repository.
- Establish a repository shape that supports code review, automated testing, and GitHub-based development.

## Non-Goals

- Replacing or redesigning vendor SDK startup sequences.
- Building a Linux kernel driver framework.
- Building a dynamic plugin system in the first phase.
- Supporting arbitrary platform-specific shortcuts inside application or component code.

## Constraints

- Implementation language is standard C.
- Linux support is user-space only.
- RTOS support is integrated on top of the original vendor SDK.
- Linux support is integrated on top of standard Linux user-space APIs.
- Application code should not require platform-specific source changes when moving between supported targets.
- Existing project assets should be preserved and reorganized rather than discarded.

## Success Criteria

- One application-facing API surface is shared by RTOS and Linux.
- The same `app/` code builds for RTOS and Linux by switching platform selection and configuration.
- Platform differences are isolated inside `platforms/*`.
- RTOS vendor SDK code remains outside framework core layers.
- Linux integration does not introduce a fake vendor-SDK layer.
- Public APIs are stable enough to support automated contract tests across platforms.

## Architecture Summary

The framework uses five layers with strict dependency direction:

`app -> core -> components -> osal/hal -> platforms/* -> vendor sdk or linux standard interfaces`

### Layer 1: Application

`app/` contains product logic, state machines, GUI startup, and application entry functions.

Rules:

- Must not include vendor SDK headers.
- Must not include Linux platform headers such as `pthread.h`, `sys/ioctl.h`, or `unistd.h`.
- Must not contain platform `#ifdef` branches.

### Layer 2: Framework Components

`components/` contains reusable services and business-facing components such as logging, events, timers, config, device management, file access, and networking.

Existing modules such as `recipe_parser` and `user_data` are preserved and moved into this layer as business components.

Rules:

- May depend on `osal/include`, `hal/include`, and common configuration headers.
- Must not directly depend on `platforms/*`.
- Must not contain vendor SDK or Linux-native headers.

### Layer 2.5: Framework Core

`core/` contains framework bootstrap, component initialization orchestration, global lifecycle entry points, and the public application-facing bootstrap header.

Rules:

- May depend on `components/`, `osal/include`, `hal/include`, and common configuration headers.
- Must not contain platform-native headers.
- Owns `ep_framework_init()` and related lifecycle orchestration.

### Layer 3: Unified API Layer

This layer defines the stable framework-facing interfaces.

It contains:

- `OSAL`: threads, mutexes, semaphores, queues, time, memory
- `HAL`: GPIO, UART, I2C, SPI, PWM, ADC
- platform-level services used by components such as file, network, and system information

Rules:

- Public headers must be platform-neutral.
- Public headers must not include RTOS headers, Linux system headers, or vendor SDK headers.
- The API must stay stable while platform implementations evolve underneath.

### Layer 4: Platform Packages

`platforms/*` contains all platform-specific adaptation code.

This is the only layer allowed to:

- include vendor SDK headers
- include Linux platform/system headers
- map unified APIs to RTOS or Linux primitives
- implement board-specific resource mapping

Platform packages are organized by platform family, not by every single board.

### Layer 5: Base Dependencies

This layer contains:

- RTOS vendor SDKs
- Linux standard user-space interfaces

RTOS vendor SDKs remain intact and are stored separately from framework code. Linux integrations depend directly on standard interfaces such as `pthread`, `poll`, `epoll`, `socket`, `termios`, `ioctl`, device nodes, and filesystem APIs.

## Repository Structure

The target repository structure is:

```text
embedded-platform-core/
├── CMakeLists.txt
├── README.md
├── LICENSE
├── .gitignore
├── cmake/
│   ├── modules/
│   ├── toolchains/
│   └── presets/
├── docs/
│   ├── architecture/
│   ├── porting/
│   ├── testing/
│   ├── decisions/
│   └── superpowers/
│       └── specs/
├── app/
│   ├── include/
│   └── src/
├── core/
│   ├── include/
│   └── src/
├── components/
│   ├── log/
│   ├── event/
│   ├── timer/
│   ├── config/
│   ├── device/
│   ├── file/
│   ├── net/
│   ├── recipe_parser/
│   └── user_data/
├── osal/
│   ├── include/
│   └── src/
├── hal/
│   ├── include/
│   └── src/
├── platforms/
│   ├── rtos/
│   │   ├── common/
│   │   └── <vendor>_<chip_family>/
│   │       ├── CMakeLists.txt
│   │       ├── startup/
│   │       ├── osal_port/
│   │       ├── hal_port/
│   │       ├── component_port/
│   │       ├── board/
│   │       │   ├── <board_a>/
│   │       │   └── <board_b>/
│   │       └── config/
│   └── linux/
│       ├── common/
│       └── <soc_family>/
│           ├── CMakeLists.txt
│           ├── startup/
│           ├── osal_port/
│           ├── hal_port/
│           ├── component_port/
│           ├── board/
│           │   ├── <board_a>/
│           │   └── <board_b>/
│           └── config/
├── vendor/
│   └── rtos/
│       └── <vendor_sdk>/
│           ├── sdk/
│           └── patches/
├── third_party/
│   └── external/
│       ├── EasyLogger/
│       └── lvgl/
├── config/
│   ├── common/
│   ├── feature/
│   └── profiles/
├── tests/
│   ├── host_unit/
│   ├── api_contract/
│   ├── integration/
│   └── target_smoke/
├── tools/
│   ├── scripts/
│   └── ci/
└── examples/
```

## Platform Package Granularity

Platform packages are created at platform-family level, not per board.

### RTOS

RTOS package naming:

`platforms/rtos/<vendor>_<chip_family>/`

Use a new RTOS platform package only when the underlying SDK integration, BSP behavior, or driver adaptation approach is materially different.

### Linux

Linux package naming:

`platforms/linux/<soc_family>/`

Use a new Linux platform package when the user-space integration model or board-facing resource structure materially differs.

### Board Layer

Board-specific differences belong under:

- `board/<board_name>/`
- `config/<board_name>.cmake`

Board variations should not create a new platform package unless they require a different adaptation architecture.

## OSAL API Organization

The OSAL public headers are:

```text
osal/include/
├── ep_osal_types.h
├── ep_osal_err.h
├── ep_osal_thread.h
├── ep_osal_mutex.h
├── ep_osal_sem.h
├── ep_osal_queue.h
├── ep_osal_time.h
└── ep_osal_mem.h
```

Rules:

- Prefix all public types and functions with `ep_`.
- Types use `_t`.
- Enumerations use `_e`.
- Functions use `ep_<module>_<action>`.
- Errors are unified under values such as `EP_OK`, `EP_ERR_INVAL`, `EP_ERR_TIMEOUT`, `EP_ERR_BUSY`, and `EP_ERR_UNSUPPORTED`.

Examples:

- `ep_thread_t`
- `ep_mutex_t`
- `ep_thread_create()`
- `ep_mutex_lock()`

## HAL API Organization

The HAL public headers are:

```text
hal/include/
├── ep_hal_types.h
├── ep_hal_err.h
├── ep_hal_gpio.h
├── ep_hal_uart.h
├── ep_hal_i2c.h
├── ep_hal_spi.h
├── ep_hal_pwm.h
└── ep_hal_adc.h
```

The preferred HAL model is handle-based rather than a platform-number-based raw API.

Example usage pattern:

```c
ep_uart_t *uart = ep_uart_open("uart0");
ep_uart_write(uart, buf, len);
ep_uart_read(uart, buf, len, timeout_ms);
ep_uart_close(uart);
```

This allows:

- RTOS implementations to wrap SDK-managed device objects
- Linux implementations to wrap file descriptors or other user-space handles
- application code to stay identical across platforms

GPIO and similar peripherals should also use a descriptor or handle model rather than exposing platform-native numbering schemes directly to applications.

## Startup and Initialization Flow

The unified startup path is:

```text
platform startup -> ep_platform_boot() -> ep_framework_init() -> app_main()
```

### RTOS Startup

RTOS vendor startup remains intact:

```text
vendor startup
-> RTOS init or vendor main
-> platforms/rtos/.../startup/app_start.c
-> ep_platform_boot()
-> ep_framework_init()
-> app_main()
```

### Linux Startup

Linux uses a user-space main entry:

```text
platforms/linux/.../startup/main.c
-> ep_platform_boot()
-> ep_framework_init()
-> app_main()
```

### Responsibility Boundaries

`startup/`

- bridges into the framework
- contains no business logic

`ep_platform_boot()`

- performs early board initialization
- registers platform devices
- initializes OSAL and HAL ports
- loads board-level configuration

`ep_framework_init()`

- initializes logging
- initializes event and timer systems
- initializes config and device management
- initializes file and network components

`app_main()`

- starts business tasks or threads
- starts GUI
- enters product-specific control flow

## Hard Rules

1. `app/` and `components/` must not directly include vendor SDK or Linux platform headers.
2. `app/` and `components/` must not contain platform `#ifdef` branches.
3. Only `platforms/*` may map unified APIs onto platform-native APIs.
4. `ep_platform_boot()` must not depend on `app/`.
5. `ep_framework_init()` must not include platform-native headers.
6. Linux must not be modeled as a vendor-SDK platform.

## Failure Handling

- If `ep_platform_boot()` fails, startup stops and the platform error is reported.
- If `ep_framework_init()` fails, application startup stops and enters a safe failure path.
- If application modules fail inside `app_main()`, behavior is handled by application policy such as degrade, retry, or exit.

## Build and Configuration Direction

The build system should use CMake as the top-level orchestrator.

Expected capabilities:

- select target platform package
- select board profile
- build shared framework code once per target
- keep RTOS vendor integration and Linux user-space integration under one project layout

Configuration layers:

- `config/common/` for cross-platform defaults
- `config/feature/` for feature toggles
- `config/profiles/` for product profiles
- `platforms/*/.../config/` for platform and board selection

## Testing Strategy

Testing is part of the framework definition, not a later add-on.

### `tests/host_unit/`

Host-side unit tests for platform-neutral logic, parsers, and common components.

### `tests/api_contract/`

Cross-platform contract tests that verify identical public API behavior on RTOS and Linux implementations.

### `tests/integration/`

Framework integration tests for component startup ordering, registration, and dependency wiring.

### `tests/target_smoke/`

Target-side smoke tests that verify boot, basic driver access, and minimal application startup on real boards or target environments.

## Repository Workflow Expectations

The repository is intended for GitHub-based development.

Expected workflow:

- Git repository with `main` as the protected stable branch
- feature branches for implementation work
- pull requests for changes to public APIs, adaptation layers, and common components
- code review for architecture, interface stability, and regression risk
- CI for build, unit tests, contract tests, and static checks

The framework should be structured so these workflows are easy to apply from the start.

## Existing Asset Migration Direction

The current local project already contains placeholders and assets that should be preserved where practical:

- `app/gui` remains under the application layer
- `components/recipe_parser` remains a component
- `components/user_data` remains a component
- `third_party/EasyLogger` moves under `third_party/external/EasyLogger`
- `third_party/lvgl` moves under `third_party/external/lvgl`

This design does not require a blank-slate rewrite.

## Initial Implementation Scope

The first implementation cycle should establish:

- repository skeleton
- top-level CMake structure
- public OSAL headers
- public HAL headers
- one RTOS platform package skeleton
- one Linux platform package skeleton
- unified startup flow
- minimal smoke application path from startup to `app_main()`

This is enough to prove the architecture before expanding more components and drivers.
