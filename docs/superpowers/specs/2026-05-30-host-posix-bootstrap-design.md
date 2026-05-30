# Host POSIX Bootstrap Design

## Overview

This design adds a small host-side POSIX platform package so the framework can be
developed and verified on macOS and Ubuntu before real RTOS board adaptation.

The host platform is not a product target. It is a fast validation target for
`app/`, `core/`, public OSAL/HAL contracts, and platform-neutral components.
Real ArtInChip Luban-Lite support remains a later RTOS platform package under
`platforms/rtos/`.

## Goals

- Provide a clear Mac/Ubuntu host validation target.
- Keep `app/`, `core/`, and future `components/` free of platform-native headers.
- Let developers run the framework bootstrap locally with CMake.
- Create a safe place for POSIX-backed OSAL implementations and HAL stubs.
- Preserve the later Luban-Lite adaptation path without mixing SDK details into
  host code.

## Non-Goals

- Do not adapt ArtInChip Luban-Lite in this step.
- Do not add RT-Thread, vendor SDK, or board-specific code.
- Do not replace the existing RTOS/Linux demo packages yet.
- Do not implement complete OSAL/HAL behavior in the first bootstrap step.
- Do not treat macOS as a production embedded platform.

## Platform Roles

The project should distinguish three environments:

```text
macOS host
  Local development, pytest, CMake bootstrap, component tests, POSIX validation.

Ubuntu host
  Local development plus ArtInChip SDK build host for later Luban-Lite work.

ArtInChip Luban-Lite target
  Real RTOS/RT-Thread firmware target, adapted later under platforms/rtos/.
```

Ubuntu is a development machine in the current plan, not the board operating
system. If a future product runs Linux on the target board, it should be modeled
as a separate Linux target package.

## Repository Shape

Add a host platform package:

```text
platforms/host/
├── common/
└── posix/
    ├── CMakeLists.txt
    ├── startup/
    │   └── main.c
    ├── osal_port/
    │   └── ep_host_osal_stub.c
    ├── hal_port/
    │   └── ep_host_hal_stub.c
    ├── component_port/
    │   └── ep_host_component_stub.c
    └── config/
        └── host_posix.cmake
```

The first implementation may keep the port files as stubs. Later PRs can replace
or split them as real OSAL modules are implemented.

## Build Model

The top-level CMake should include the host POSIX package as a normal build
target. The first target can be named:

```text
ep_platform_host_posix
```

The target links:

```text
ep_core
ep_app
```

The host executable entry path is:

```text
platforms/host/posix/startup/main.c
-> ep_framework_start()
-> ep_platform_boot()
-> ep_framework_init()
-> app_main()
```

`ep_platform_boot()` for the first host bootstrap should return success and
avoid platform-specific side effects.

## Layering Rules

Host POSIX code may include system headers such as:

```text
pthread.h
time.h
unistd.h
stdlib.h
stdio.h
```

Those headers must stay inside `platforms/host/posix/` or host-only tests.

The following layers must not include POSIX, Linux, RT-Thread, or vendor SDK
headers:

```text
app/
core/
components/
osal/include/
hal/include/
```

## Incremental PR Sequence

The host path should be built in small reviewable steps:

1. Add `platforms/host/posix` bootstrap target.
2. Add host OSAL time and memory implementations.
3. Add host OSAL mutex, semaphore, thread, and queue implementations.
4. Add a minimal logging component that works on host.
5. Add event and timer components on top of OSAL.
6. Add HAL mock or stub modules for host-side tests.
7. Write the ArtInChip Luban-Lite adaptation design.
8. Add `platforms/rtos/artinchip_luban_lite` skeleton.

Each PR should keep a narrow boundary and include tests that can run on macOS
and GitHub Actions.

## Testing Strategy

The first host bootstrap PR should add or update tests to verify:

- `platforms/host/posix` exists.
- The host target is mentioned in the top-level CMake graph.
- CMake configure/build succeeds on the development machine.
- The generated host executable runs and exits with status `0`.

Existing validation remains required:

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
```

Later OSAL implementations should add API contract tests and host unit tests
before implementation.

## Luban-Lite Boundary

ArtInChip Luban-Lite should be adapted separately as an RTOS platform package:

```text
platforms/rtos/artinchip_luban_lite/
vendor/rtos/artinchip_luban_lite/
```

Expected mappings for later work:

```text
ep_osal_thread -> rt_thread_*
ep_osal_mutex  -> rt_mutex_*
ep_osal_sem    -> rt_sem_*
ep_osal_queue  -> rt_mq_* or rt_mb_*
ep_osal_time   -> rt_tick / rt_timer
ep_osal_mem    -> rt_malloc / rt_free
ep_hal_gpio    -> RT-Thread PIN device or ArtInChip GPIO driver
ep_hal_uart    -> RT-Thread serial device
ep_hal_i2c     -> RT-Thread I2C device
ep_hal_spi     -> RT-Thread SPI device
```

No Luban-Lite SDK headers should be included by host POSIX code.

## Success Criteria

- Developers can build and run a named host POSIX executable on macOS.
- The host package has a clear location separate from RTOS and target Linux
  packages.
- Public framework layers remain platform-neutral.
- The next OSAL and component PRs have a stable host target for fast feedback.
- The later Luban-Lite adaptation path remains explicit and isolated.
