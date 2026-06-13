# Running Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal recipe running page that every Home carousel recipe can open, with a Settings-style top-left back button returning to Home.

**Architecture:** The running page is a normal page-manager page, registered from `app_ui_create()` and built in its own `running_page.c/h` files. Home carousel center-slot clicks navigate to `APP_PAGE_RUNNING` with history enabled, so the running page back button uses `page_manager_back()` without coupling directly to Home.

**Tech Stack:** C, CMake, LVGL 9, existing `page_manager`, existing settings UI common helpers, pytest source-inspection host tests.

---

## File Structure

- Create `app/ui/pages/running_page.h`: declares the running page create/event/destroy callbacks.
- Create `app/ui/pages/running_page.c`: creates a black 800x480 screen, adds a top-left Settings-style back button, and releases page state.
- Modify `app/ui/pages/app_pages.h`: adds `APP_PAGE_RUNNING`.
- Modify `app/ui/app_ui.c`: includes `running_page.h` and registers `APP_PAGE_RUNNING`.
- Modify `app/ui/pages/home_page.c`: adds a center recipe click handler and makes the center slot clickable.
- Modify `app/CMakeLists.txt`: builds `ui/pages/running_page.c`.
- Modify `tests/host_unit/test_app_page_manager.py`: adds source-inspection coverage for the new page, registration, navigation, and back-button metrics.
- Modify `tests/host_unit/test_app_portable_lvgl_ui.py`: keeps the portable UI source/export checks aware of `running_page.c`.
- Modify `cmake/modules/ep_export_targets.cmake`, `platforms/host/posix/CMakeLists.txt`, and `tools/scripts/export_sdk_ep_package.sh`: includes the running page in the same export/demo source lists as existing app UI pages.

## Task 1: Source-Inspection Test For Running Page Contract

**Files:**
- Modify: `tests/host_unit/test_app_page_manager.py`
- Modify: `tests/host_unit/test_app_portable_lvgl_ui.py`

- [ ] **Step 1: Add failing page-manager test**

Append this test to `tests/host_unit/test_app_page_manager.py`:

```python
def test_home_recipe_opens_minimal_running_page_with_back_button():
    app_pages = _read("app/ui/pages/app_pages.h")
    app_ui = _read("app/ui/app_ui.c")
    app_cmake = _read("app/CMakeLists.txt")
    home_page = _read("app/ui/pages/home_page.c")
    running_header = _read("app/ui/pages/running_page.h")
    running_page = _read("app/ui/pages/running_page.c")

    assert "APP_PAGE_RUNNING" in app_pages
    assert '#include "pages/running_page.h"' in app_ui
    assert "page_manager_register(APP_PAGE_RUNNING" in app_ui
    assert "running_page_create" in app_ui
    assert "running_page_event" in app_ui
    assert "running_page_destroy" in app_ui
    assert "ui/pages/running_page.c" in app_cmake

    assert "static void home_page_recipe_clicked(lv_event_t *event)" in home_page
    assert "page_manager_switch(APP_PAGE_RUNNING, LV_SCR_LOAD_ANIM_MOVE_LEFT, 180, true)" in home_page
    assert "lv_obj_add_event_cb(slot->container, home_page_recipe_clicked, LV_EVENT_CLICKED, state)" in home_page
    assert "slot_index == HOME_PAGE_CENTER_SLOT" in home_page

    assert "lv_obj_t *running_page_create(page_manager_page_ctx_t *ctx);" in running_header
    assert "void running_page_event(page_manager_page_ctx_t *ctx, uint32_t code, uint32_t wparam, uint32_t lparam);" in running_header
    assert "void running_page_destroy(page_manager_page_ctx_t *ctx);" in running_header
    assert "settings_common_style_screen(screen)" in running_page
    assert "SETTINGS_PAGE_BACK_ICON_NAME" in running_page
    assert "SETTINGS_PAGE_BACK_X" in running_page
    assert "SETTINGS_PAGE_BACK_Y" in running_page
    assert "SETTINGS_PAGE_BACK_SIZE" in running_page
    assert "page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180)" in running_page
```

- [ ] **Step 2: Extend portable UI test**

In `tests/host_unit/test_app_portable_lvgl_ui.py`, update the existing tests with these exact assertions:

```python
assert '#include "pages/running_page.h"' in text
assert "page_manager_register(APP_PAGE_RUNNING" in text
```

Add `running_page = REPO_ROOT / "app/ui/pages/running_page.c"` near the existing `home_page` path, read it as `running_text`, and check the same portability forbidden tokens against `running_text`.

In `test_app_cmake_builds_portable_ui_without_host_port_dependency()`, add:

```python
assert "ui/pages/running_page.c" in cmake
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py::test_home_recipe_opens_minimal_running_page_with_back_button tests/host_unit/test_app_portable_lvgl_ui.py -q
```

Expected: FAIL because `app/ui/pages/running_page.h` and `app/ui/pages/running_page.c` do not exist yet.

## Task 2: Add Running Page And Register It

**Files:**
- Create: `app/ui/pages/running_page.h`
- Create: `app/ui/pages/running_page.c`
- Modify: `app/ui/pages/app_pages.h`
- Modify: `app/ui/app_ui.c`
- Modify: `app/CMakeLists.txt`

- [ ] **Step 1: Add running page header**

Create `app/ui/pages/running_page.h`:

```c
#ifndef RUNNING_PAGE_H
#define RUNNING_PAGE_H

#include "page_manager.h"

#include <stdint.h>

lv_obj_t *running_page_create(page_manager_page_ctx_t *ctx);
void running_page_event(page_manager_page_ctx_t *ctx, uint32_t code, uint32_t wparam, uint32_t lparam);
void running_page_destroy(page_manager_page_ctx_t *ctx);

#endif
```

- [ ] **Step 2: Add running page source**

Create `app/ui/pages/running_page.c`:

```c
#include "pages/running_page.h"

#include "lvgl.h"
#include "pages/settings_common.h"

#include <stdlib.h>

typedef struct {
    lv_obj_t *screen;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
} running_page_state_t;

static void running_page_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

lv_obj_t *running_page_create(page_manager_page_ctx_t *ctx)
{
    running_page_state_t *state;
    lv_obj_t *screen;

    (void)ctx;

    state = (running_page_state_t *)calloc(1u, sizeof(*state));
    if (state == NULL) {
        return NULL;
    }

    screen = lv_obj_create(NULL);
    if (screen == NULL) {
        free(state);
        return NULL;
    }

    state->screen = screen;
    lv_obj_set_user_data(screen, state);
    settings_common_style_screen(screen);

    if (!settings_common_create_icon_button(screen,
                                            SETTINGS_PAGE_BACK_ICON_NAME,
                                            state->back_src,
                                            sizeof(state->back_src),
                                            SETTINGS_PAGE_BACK_X,
                                            SETTINGS_PAGE_BACK_Y,
                                            SETTINGS_PAGE_BACK_SIZE,
                                            running_page_back_clicked)) {
        lv_obj_delete(screen);
        free(state);
        return NULL;
    }

    return screen;
}

void running_page_event(page_manager_page_ctx_t *ctx, uint32_t code, uint32_t wparam, uint32_t lparam)
{
    (void)ctx;
    (void)code;
    (void)wparam;
    (void)lparam;
}

void running_page_destroy(page_manager_page_ctx_t *ctx)
{
    running_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (running_page_state_t *)lv_obj_get_user_data(ctx->screen);
    free(state);
    lv_obj_set_user_data(ctx->screen, NULL);
}
```

- [ ] **Step 3: Register page id and page callbacks**

In `app/ui/pages/app_pages.h`, add:

```c
    APP_PAGE_RUNNING = 9,
```

In `app/ui/app_ui.c`, add:

```c
#include "pages/running_page.h"
```

Register after `APP_PAGE_HOME`:

```c
    rc = page_manager_register(APP_PAGE_RUNNING, running_page_create, running_page_event, running_page_destroy);
    if (rc != 0) {
        return rc;
    }
```

In `app/CMakeLists.txt`, add:

```cmake
  ui/pages/running_page.c
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py::test_home_recipe_opens_minimal_running_page_with_back_button tests/host_unit/test_app_portable_lvgl_ui.py -q
```

Expected: tests still FAIL because Home does not yet navigate to `APP_PAGE_RUNNING`.

## Task 3: Wire Home Center Recipe Click To Running Page

**Files:**
- Modify: `app/ui/pages/home_page.c`

- [ ] **Step 1: Add recipe click callback**

Add this callback near `home_page_settings_clicked()`:

```c
static void home_page_recipe_clicked(lv_event_t *event)
{
    home_page_state_t *state;

    state = (home_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL || state->recipe_count == 0u) {
        return;
    }

    (void)page_manager_switch(APP_PAGE_RUNNING, LV_SCR_LOAD_ANIM_MOVE_LEFT, 180, true);
}
```

- [ ] **Step 2: Make only the center carousel slot clickable**

In `home_page_create_slot(...)`, after configuring `slot->container`, add:

```c
    if (slot_index == HOME_PAGE_CENTER_SLOT) {
        lv_obj_add_flag(slot->container, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(slot->container, home_page_recipe_clicked, LV_EVENT_CLICKED, state);
    }
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py::test_home_recipe_opens_minimal_running_page_with_back_button tests/host_unit/test_app_portable_lvgl_ui.py -q
```

Expected: PASS.

## Task 4: Build And Full Relevant Verification

**Files:**
- Modify: `cmake/modules/ep_export_targets.cmake`
- Modify: `platforms/host/posix/CMakeLists.txt`
- Modify: `tools/scripts/export_sdk_ep_package.sh`
- Modify: `tests/host_unit/test_app_page_manager.py`
- Modify: `tests/host_unit/test_app_portable_lvgl_ui.py`

- [ ] **Step 1: Add running page to export/demo source lists**

In `cmake/modules/ep_export_targets.cmake`, add:

```cmake
  ${CMAKE_SOURCE_DIR}/app/ui/pages/running_page.c
```

In `platforms/host/posix/CMakeLists.txt`, add:

```cmake
    ${CMAKE_SOURCE_DIR}/app/ui/pages/running_page.c
```

In `tools/scripts/export_sdk_ep_package.sh`, add:

```text
app/ui/pages/running_page.c
```

- [ ] **Step 2: Extend export tests**

In `tests/host_unit/test_app_portable_lvgl_ui.py`, assert that `running_page.c` is included in static and SDK export lists:

```python
assert "${CMAKE_SOURCE_DIR}/app/ui/pages/running_page.c" in host_export
assert "app/ui/pages/running_page.c" in sdk_export
```

In `tests/host_unit/test_app_page_manager.py`, include `app/ui/pages/running_page.c` in the settings/UI source export loop so the host demo source list stays in sync:

```python
"app/ui/pages/running_page.c",
```

- [ ] **Step 3: Run focused UI tests**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py tests/host_unit/test_app_portable_lvgl_ui.py -q
```

Expected: PASS.

- [ ] **Step 4: Build host app**

Run:

```bash
./build.sh build-host
```

Expected: command exits 0 and builds `ep_host_app`.

- [ ] **Step 5: Commit implementation**

Commit only files changed for this feature:

```bash
git add app/CMakeLists.txt app/ui/app_ui.c app/ui/pages/app_pages.h app/ui/pages/home_page.c app/ui/pages/running_page.c app/ui/pages/running_page.h cmake/modules/ep_export_targets.cmake platforms/host/posix/CMakeLists.txt tools/scripts/export_sdk_ep_package.sh tests/host_unit/test_app_page_manager.py tests/host_unit/test_app_portable_lvgl_ui.py docs/superpowers/plans/2026-06-13-running-page.md
git commit -m "Implement minimal recipe running page"
```
