# Portable App LVGL UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a shared `app/ui` LVGL page layer so business UI code can be written and tested on macOS, then exported and built on AIC Luban-Lite without rewriting platform code.

**Architecture:** `app/ui` owns portable page creation and may include standard `lvgl.h`; `components/ui` owns only LVGL lifecycle; host macOS owns SDL2 display/input; AIC Luban-Lite owns SDK LVGL display/input. SDK export compiles `app/ui` into `libep_app_core.a` with Luban-Lite LVGL headers, but still excludes `components/ui/src/ep_ui.c`.

**Tech Stack:** C11, CMake, LVGL 9.x, pytest, shell SDK export scripts.

---

### Task 1: Test Portable UI Boundary

**Files:**
- Create: `tests/host_unit/test_app_portable_lvgl_ui.py`
- Modify: `tests/host_unit/test_host_macos_sdl2_ui_port.py`
- Modify: `tests/host_unit/test_target_firmware_build.py`

- [ ] Add tests that require `app/ui/app_ui.h` and `app/ui/app_ui.c`.
- [ ] Assert `app_ui.h` exposes `int app_ui_create(void);` without including LVGL, SDL2, RT-Thread or AIC headers.
- [ ] Assert `app_ui.c` creates LVGL widgets with standard `lvgl.h` and no platform headers.
- [ ] Assert host startup calls `app_ui_create()` instead of creating LVGL labels directly.
- [ ] Assert SDK export includes `app/ui/app_ui.c` and SDK LVGL include paths, while still excluding `components/ui/src/ep_ui.c`.
- [ ] Run targeted pytest and confirm RED failure.

### Task 2: Implement Portable UI Layer

**Files:**
- Create: `app/ui/app_ui.h`
- Create: `app/ui/app_ui.c`
- Modify: `app/CMakeLists.txt`
- Modify: `platforms/host/posix/startup/main.c`
- Modify: `platforms/host/posix/demos/lvgl_demo_main.c`
- Modify: `platforms/host/posix/CMakeLists.txt`

- [ ] Add `app_ui_create()` that creates a minimal LVGL title and status text on `lv_screen_active()`.
- [ ] Keep the public header free of LVGL and platform-native headers.
- [ ] Wire host startup/demo to call `app_ui_create()` after `ep_ui_init()` and host SDL2 port init.
- [ ] Keep `ep_app` free of host-specific compile definitions and platform ports.
- [ ] Run targeted pytest and CMake build.

### Task 3: Export App UI To Host And SDK Packages

**Files:**
- Modify: `cmake/modules/ep_export_targets.cmake`
- Modify: `tools/scripts/export_ep_package.sh`
- Modify: `tools/scripts/export_sdk_ep_package.sh`
- Modify: minimal repo fixtures in affected pytest files.

- [ ] Add `app/ui` headers to package exports.
- [ ] Add `app/ui/app_ui.c` to host static export target and SDK export sources.
- [ ] Add Luban-Lite LVGL v9 include directories to SDK compile flags when present.
- [ ] Keep SDK export independent from host prebuilt `ep_thirdparty_lvgl`.
- [ ] Run export and firmware build tests.

### Task 4: Document The Workflow

**Files:**
- Modify: `docs/porting/app-business-skeleton.md`
- Modify: `docs/porting/luban-lite-compatibility-overview.md`
- Modify: `docs/development/roadmap.md`

- [ ] Explain where business logic, app UI, LVGL lifecycle, and platform display/input live.
- [ ] Explain macOS edit/debug flow and AIC export/build flow.
- [ ] Mention RTOS SDK LVGL is reused from the vendor SDK, while Linux LVGL may live in a component/sub-repo.

### Task 5: Verify, Commit, PR

**Files:**
- All changed files.

- [ ] Run targeted pytest for app UI, host UI, app skeleton, target firmware export, package export and docs.
- [ ] Run `cmake --build` for `ep_app_core_export` and `ep_platform_host_posix`.
- [ ] Run `./build.sh validate-targets`.
- [ ] Commit with a Chinese message.
- [ ] Push branch and create a Chinese PR.
