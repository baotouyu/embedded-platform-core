# embedded-platform-core

A portable embedded platform framework for RTOS and Linux, with unified OS, driver, and component abstractions.

一个面向 RTOS 和 Linux 的可移植嵌入式平台框架，保留原厂 SDK，并提供统一的 OS、驱动和组件抽象层。

## Overview

This repository is the bootstrap of a cross-platform embedded framework written in standard C.

Current design goals:

- keep RTOS vendor SDKs intact instead of rewriting vendor startup paths
- use Linux user-space standard interfaces instead of a Linux vendor SDK layer
- expose unified public APIs for OS abstraction and driver abstraction
- isolate platform differences inside platform packages
- let upper application code move across supported targets with minimal or no source changes

The current repository state is an initial framework scaffold:

- top-level CMake bootstrap is in place
- framework bootstrap core is in place
- public OSAL and HAL header surfaces are in place
- RTOS and Linux demo platform skeletons are in place
- GitHub workflow templates and CI skeleton are in place

## Architecture

The framework is organized into layered responsibilities:

`app -> core -> components -> osal/hal -> platforms/* -> vendor sdk or linux standard interfaces`

### `app/`

Application entry and product logic.

- should not directly include vendor SDK headers
- should not directly include Linux-native platform headers
- should not contain platform-specific `#ifdef` branches

### `core/`

Framework lifecycle and startup coordination.

- owns `ep_framework_init()` and `ep_framework_start()`
- bridges application startup with platform bootstrap

### `components/`

Reusable cross-platform services and business-facing modules.

Current component skeletons include:

- `log`
- `event`
- `timer`
- `config`
- `device`
- `file`
- `net`

### `osal/`

Public OS abstraction layer.

Current public headers:

- `ep_osal_types.h`
- `ep_osal_err.h`
- `ep_osal_thread.h`
- `ep_osal_mutex.h`
- `ep_osal_sem.h`
- `ep_osal_queue.h`
- `ep_osal_time.h`
- `ep_osal_mem.h`

### `hal/`

Public hardware abstraction layer.

Current public headers:

- `ep_hal_types.h`
- `ep_hal_err.h`
- `ep_hal_gpio.h`
- `ep_hal_uart.h`
- `ep_hal_i2c.h`
- `ep_hal_spi.h`
- `ep_hal_pwm.h`
- `ep_hal_adc.h`

### `platforms/`

Platform-specific adaptation packages.

Current demo packages:

- `platforms/rtos/demo_family`
- `platforms/linux/demo_family`

Each package contains:

- `startup/`
- `osal_port/`
- `hal_port/`
- `component_port/`
- `board/`
- `config/`

### `vendor/`

Reserved location for RTOS vendor SDKs and patches.

Linux user-space integration is not modeled as a vendor SDK layer.

## Current Repository Structure

```text
embedded-platform-core/
├── .github/
├── app/
├── cmake/
├── components/
├── config/
├── core/
├── docs/
├── examples/
├── hal/
├── osal/
├── platforms/
│   ├── linux/
│   │   ├── common/
│   │   └── demo_family/
│   └── rtos/
│       ├── common/
│       └── demo_family/
├── tests/
│   ├── api_contract/
│   ├── host_unit/
│   ├── integration/
│   └── target_smoke/
├── third_party/
│   └── external/
├── tools/
└── vendor/
```

## Build Status

Current bootstrap supports:

- top-level CMake configure
- framework core/app targets
- public OSAL/HAL interface targets
- RTOS demo platform static target
- Linux demo platform executable target

This is still a scaffold stage, not a production-ready board integration.

## Tests

The repository currently includes bootstrap tests for:

- repository skeleton existence
- top-level CMake bootstrap structure
- framework bootstrap core wiring
- OSAL public headers
- HAL public headers
- RTOS/Linux platform bootstrap skeletons
- GitHub workflow files

Contract tests have been strengthened so OSAL and HAL public headers are checked as standalone compilable headers, not just text placeholders.

## GitHub Workflow

The repository includes:

- `CODEOWNERS`
- pull request template
- issue templates
- GitHub Actions CI skeleton

Current CI runs:

- `pytest tests/host_unit tests/api_contract -v`

## Current Constraints

- implementation language is standard C
- Linux support is user-space only
- RTOS side is expected to stay on top of vendor SDK startup and driver models
- framework APIs are currently scaffold-level and will continue evolving as real platforms are integrated

## Next Steps

The next practical steps after this bootstrap phase are:

1. replace `demo_family` platform placeholders with real RTOS and Linux platform packages
2. wire board/config selection into platform build flow
3. connect real OSAL and HAL backend implementations
4. add stronger build and target smoke coverage
5. start integrating actual product/application modules on top of the stable public interfaces

## Design References

Repository design and planning artifacts are stored under:

- `docs/superpowers/specs/`
- `docs/superpowers/plans/`

These documents capture the current architecture decisions and implementation sequence used to bootstrap this repository.
