# Settings Selection List Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reusable settings selection list and a language selection page whose confirm/back controls return to settings, while switching related borders to gray.

**Architecture:** Keep the implementation inside the existing LVGL app pages. Add a language page id and registration, route Settings > Language to it, and implement a small file-local reusable selection-list helper in `settings_page.c` that can later be reused by a sleep page with a different option array and height.

**Tech Stack:** C, LVGL, existing `page_manager`, existing `ui_style` SourceHan/TinyTTF fonts, pytest source-inspection tests.

---

### Task 1: Add Failing Source-Inspection Tests

**Files:**
- Modify: `tests/host_unit/test_app_page_manager.py`

- [ ] **Step 1: Write the failing tests**

Add these test functions near the existing settings-page tests in `tests/host_unit/test_app_page_manager.py`:

```python
def test_language_page_is_registered_and_reachable():
    app_pages = (REPO_ROOT / "app/ui/pages/app_pages.h").read_text()
    app_ui = (REPO_ROOT / "app/ui/app_ui.c").read_text()
    settings_page = (REPO_ROOT / "app/ui/pages/settings_page.c").read_text()

    assert "APP_PAGE_LANGUAGE" in app_pages
    assert "page_manager_register(APP_PAGE_LANGUAGE" in app_ui
    assert "settings_language_page_create" in app_ui
    assert "page_manager_switch(APP_PAGE_LANGUAGE" in settings_page
    assert "SETTINGS_PAGE_ACTION_LANGUAGE" in settings_page


def test_settings_selection_list_reusable_metrics_and_language_options():
    settings_page = (REPO_ROOT / "app/ui/pages/settings_page.c").read_text()

    assert "#define SETTINGS_SELECTION_LIST_WIDTH 369" in settings_page
    assert "#define SETTINGS_SELECTION_LIST_ROW_HEIGHT 64" in settings_page
    assert "#define SETTINGS_SELECTION_LIST_RADIUS 12" in settings_page
    assert "settings_selection_list_create(" in settings_page
    assert "settings_language_options[]" in settings_page
    for label in ["English", "简体中文", "Français", "Italiano", "Deutsch", "Русский"]:
        assert label in settings_page


def test_language_page_confirm_and_back_return_to_settings():
    settings_page = (REPO_ROOT / "app/ui/pages/settings_page.c").read_text()

    assert "settings_language_back_clicked" in settings_page
    assert "settings_language_confirm_clicked" in settings_page
    assert settings_page.count("page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180)") >= 3


def test_settings_and_user_borders_are_gray():
    settings_page = (REPO_ROOT / "app/ui/pages/settings_page.c").read_text()
    home_page = (REPO_ROOT / "app/ui/pages/home_page.c").read_text()

    assert "#define SETTINGS_PAGE_BUTTON_BORDER_COLOR 0x666666" in settings_page
    assert "#define HOME_PAGE_USER_DROPDOWN_BORDER_COLOR 0x666666" in home_page
    assert "0x43382D" not in settings_page
    assert "0x3D3734" not in home_page
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py -q
```

Expected: FAIL because `APP_PAGE_LANGUAGE`, `settings_selection_list_create`, and the gray border constants do not exist yet.

### Task 2: Add Language Page Wiring

**Files:**
- Modify: `app/ui/pages/app_pages.h`
- Modify: `app/ui/pages/settings_page.h`
- Modify: `app/ui/app_ui.c`
- Modify: `app/ui/pages/settings_page.c`
- Test: `tests/host_unit/test_app_page_manager.py`

- [ ] **Step 1: Add page id**

In `app/ui/pages/app_pages.h`, extend the enum:

```c
typedef enum {
    APP_PAGE_NONE = 0,
    APP_PAGE_HOME = 1,
    APP_PAGE_SETTINGS = 2,
    APP_PAGE_LANGUAGE = 3,
} app_page_id_t;
```

- [ ] **Step 2: Declare language page callbacks**

In `app/ui/pages/settings_page.h`, add prototypes next to the existing settings page functions:

```c
lv_obj_t *settings_language_page_create(page_manager_page_ctx_t *ctx);
void settings_language_page_destroy(page_manager_page_ctx_t *ctx);
void settings_language_page_event(page_manager_page_ctx_t *ctx,
                                  uint32_t code,
                                  uint32_t wparam,
                                  uint32_t lparam);
```

- [ ] **Step 3: Register language page**

In `app/ui/app_ui.c`, register the new page after settings registration:

```c
    rc = page_manager_register(APP_PAGE_LANGUAGE,
                               settings_language_page_create,
                               settings_language_page_event,
                               settings_language_page_destroy);
    if (rc != EP_OK) {
        return rc;
    }
```

- [ ] **Step 4: Route language settings button**

In `settings_page_item_clicked()` inside `app/ui/pages/settings_page.c`, switch on the action:

```c
    if (spec->action == SETTINGS_PAGE_ACTION_LANGUAGE) {
        (void)page_manager_switch(APP_PAGE_LANGUAGE, LV_SCR_LOAD_ANIM_MOVE_LEFT, 180, true);
    }
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py::test_language_page_is_registered_and_reachable -q
```

Expected: PASS after Task 3 creates the callback implementations; until then, the source-inspection test can pass before compile tests do.

### Task 3: Implement Reusable Selection List and Language Page

**Files:**
- Modify: `app/ui/pages/settings_page.c`
- Test: `tests/host_unit/test_app_page_manager.py`

- [ ] **Step 1: Add shared constants and types**

Add these constants near the existing settings constants:

```c
#define SETTINGS_SHARED_GRAY_BORDER_COLOR 0x666666
#define SETTINGS_SELECTION_LIST_WIDTH 369
#define SETTINGS_SELECTION_LIST_ROW_HEIGHT 64
#define SETTINGS_SELECTION_LIST_RADIUS 12
#define SETTINGS_SELECTION_LIST_X ((SETTINGS_PAGE_SCREEN_WIDTH - SETTINGS_SELECTION_LIST_WIDTH) / 2)
#define SETTINGS_SELECTION_LIST_Y 112
#define SETTINGS_SELECTION_LIST_VISIBLE_ROWS 5
#define SETTINGS_SELECTION_LIST_HEIGHT (SETTINGS_SELECTION_LIST_ROW_HEIGHT * SETTINGS_SELECTION_LIST_VISIBLE_ROWS)
#define SETTINGS_SELECTION_LIST_UNSELECTED_COLOR SETTINGS_PAGE_BUTTON_COLOR
#define SETTINGS_SELECTION_LIST_SELECTED_COLOR 0xFFFFFF
#define SETTINGS_SELECTION_LIST_SEPARATOR_COLOR 0x3A3A3A
#define SETTINGS_LANGUAGE_CONFIRM_X 720
#define SETTINGS_LANGUAGE_CONFIRM_Y 32
#define SETTINGS_LANGUAGE_CONFIRM_SIZE 48
```

Add file-local structs:

```c
typedef struct {
    const char *label;
    const char *language_code;
} settings_selection_option_t;

typedef struct {
    lv_obj_t *container;
    lv_obj_t **rows;
    lv_obj_t **labels;
    size_t option_count;
    size_t selected_index;
} settings_selection_list_t;
```

- [ ] **Step 2: Add language options**

Add this static array:

```c
static const settings_selection_option_t settings_language_options[] = {
    {"English", "en"},
    {"简体中文", "zh-CN"},
    {"Français", "fr"},
    {"Italiano", "it"},
    {"Deutsch", "de"},
    {"Русский", "ru"},
};
```

- [ ] **Step 3: Implement list refresh and row click**

Add:

```c
static void settings_selection_list_refresh(settings_selection_list_t *list)
{
    if (list == NULL) {
        return;
    }

    for (size_t i = 0u; i < list->option_count; ++i) {
        bool selected = i == list->selected_index;

        if (list->rows[i] != NULL) {
            lv_obj_set_style_bg_color(
                list->rows[i],
                lv_color_hex(selected ? SETTINGS_SELECTION_LIST_SELECTED_COLOR :
                                       SETTINGS_SELECTION_LIST_UNSELECTED_COLOR),
                LV_PART_MAIN);
            lv_obj_set_style_bg_opa(list->rows[i], LV_OPA_COVER, LV_PART_MAIN);
        }

        if (list->labels[i] != NULL) {
            lv_obj_set_style_text_color(list->labels[i],
                                        selected ? lv_color_black() : lv_color_white(),
                                        LV_PART_MAIN);
        }
    }
}

static void settings_selection_row_clicked(lv_event_t *event)
{
    settings_selection_list_t *list;
    lv_obj_t *row;

    list = (settings_selection_list_t *)lv_event_get_user_data(event);
    row = lv_event_get_current_target_obj(event);
    if (list == NULL || row == NULL) {
        return;
    }

    for (size_t i = 0u; i < list->option_count; ++i) {
        if (list->rows[i] == row) {
            list->selected_index = i;
            settings_selection_list_refresh(list);
            return;
        }
    }
}
```

- [ ] **Step 4: Implement list creation helper**

Add:

```c
static bool settings_selection_list_create(lv_obj_t *parent,
                                           settings_selection_list_t *list,
                                           const settings_selection_option_t *options,
                                           size_t option_count,
                                           size_t selected_index,
                                           int32_t x,
                                           int32_t y,
                                           int32_t visible_rows)
{
    int32_t visible_height;

    if (parent == NULL || list == NULL || options == NULL || option_count == 0u || visible_rows <= 0) {
        return false;
    }

    list->rows = (lv_obj_t **)calloc(option_count, sizeof(*list->rows));
    list->labels = (lv_obj_t **)calloc(option_count, sizeof(*list->labels));
    if (list->rows == NULL || list->labels == NULL) {
        return false;
    }

    list->option_count = option_count;
    list->selected_index = selected_index < option_count ? selected_index : 0u;
    visible_height = SETTINGS_SELECTION_LIST_ROW_HEIGHT * visible_rows;

    list->container = lv_obj_create(parent);
    if (list->container == NULL) {
        return false;
    }

    lv_obj_remove_style_all(list->container);
    lv_obj_set_pos(list->container, x, y);
    lv_obj_set_size(list->container, SETTINGS_SELECTION_LIST_WIDTH, visible_height);
    lv_obj_set_style_radius(list->container, SETTINGS_SELECTION_LIST_RADIUS, LV_PART_MAIN);
    lv_obj_set_style_bg_color(list->container, lv_color_hex(SETTINGS_SELECTION_LIST_UNSELECTED_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(list->container, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_color(list->container, lv_color_hex(SETTINGS_SHARED_GRAY_BORDER_COLOR), LV_PART_MAIN);
    lv_obj_set_style_border_width(list->container, 1, LV_PART_MAIN);
    lv_obj_set_style_clip_corner(list->container, true, LV_PART_MAIN);
    lv_obj_set_scroll_dir(list->container, LV_DIR_VER);
    lv_obj_set_scrollbar_mode(list->container, LV_SCROLLBAR_MODE_AUTO);

    for (size_t i = 0u; i < option_count; ++i) {
        lv_obj_t *row = lv_obj_create(list->container);
        lv_obj_t *label;

        if (row == NULL) {
            continue;
        }

        list->rows[i] = row;
        lv_obj_remove_style_all(row);
        lv_obj_set_pos(row, 0, (int32_t)i * SETTINGS_SELECTION_LIST_ROW_HEIGHT);
        lv_obj_set_size(row, SETTINGS_SELECTION_LIST_WIDTH, SETTINGS_SELECTION_LIST_ROW_HEIGHT);
        lv_obj_set_style_radius(row, 0, LV_PART_MAIN);
        lv_obj_set_style_border_width(row, i + 1u == option_count ? 0 : 1, LV_PART_MAIN);
        lv_obj_set_style_border_side(row, LV_BORDER_SIDE_BOTTOM, LV_PART_MAIN);
        lv_obj_set_style_border_color(row, lv_color_hex(SETTINGS_SELECTION_LIST_SEPARATOR_COLOR), LV_PART_MAIN);
        lv_obj_clear_flag(row, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(row, settings_selection_row_clicked, LV_EVENT_CLICKED, list);

        label = lv_label_create(row);
        if (label == NULL) {
            continue;
        }

        list->labels[i] = label;
        lv_obj_remove_style_all(label);
        lv_obj_set_size(label, SETTINGS_SELECTION_LIST_WIDTH, SETTINGS_SELECTION_LIST_ROW_HEIGHT);
        lv_obj_set_pos(label, 0, 0);
        lv_obj_set_style_text_font(label, ui_style_font(UI_STYLE_FONT_HOME_CENTER), LV_PART_MAIN);
        lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
        lv_obj_set_style_pad_top(label, 8, LV_PART_MAIN);
        lv_label_set_long_mode(label, LV_LABEL_LONG_CLIP);
        lv_label_set_text(label, options[i].label);
    }

    settings_selection_list_refresh(list);
    return true;
}
```

- [ ] **Step 5: Add language page state and callbacks**

Add:

```c
typedef struct {
    lv_obj_t *screen;
    settings_selection_list_t list;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
} settings_language_page_state_t;

static void settings_language_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static void settings_language_confirm_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}
```

- [ ] **Step 6: Add top icon helper and page create/destroy/event**

Add:

```c
static bool settings_language_create_icon_button(lv_obj_t *screen,
                                                 const char *icon_name,
                                                 char *src,
                                                 size_t src_size,
                                                 int32_t x,
                                                 int32_t y,
                                                 lv_event_cb_t clicked_cb)
{
    lv_obj_t *button;
    lv_obj_t *image;

    button = lv_button_create(screen);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_LANGUAGE_CONFIRM_SIZE, SETTINGS_LANGUAGE_CONFIRM_SIZE);
    lv_obj_set_pos(button, x, y);
    lv_obj_set_style_bg_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_event_cb(button, clicked_cb, LV_EVENT_CLICKED, NULL);

    if (ep_platform_lvgl_image_src(icon_name, src, src_size) != EP_OK) {
        return true;
    }

    image = lv_image_create(button);
    if (image == NULL) {
        return false;
    }

    lv_obj_remove_style_all(image);
    lv_obj_set_size(image, SETTINGS_LANGUAGE_CONFIRM_SIZE, SETTINGS_LANGUAGE_CONFIRM_SIZE);
    lv_obj_set_pos(image, 0, 0);
    lv_image_set_src(image, src);
    return true;
}

void settings_language_page_destroy(page_manager_page_ctx_t *ctx)
{
    settings_language_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (settings_language_page_state_t *)lv_obj_get_user_data(ctx->screen);
    if (state != NULL) {
        free(state->list.rows);
        free(state->list.labels);
        free(state);
    }
}

lv_obj_t *settings_language_page_create(page_manager_page_ctx_t *ctx)
{
    lv_obj_t *screen;
    settings_language_page_state_t *state;

    (void)ctx;

    state = (settings_language_page_state_t *)calloc(1u, sizeof(*state));
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
    (void)ui_style_init();
    settings_page_style_screen(screen);

    if (!settings_language_create_icon_button(screen,
                                              SETTINGS_PAGE_BACK_ICON_NAME,
                                              state->back_src,
                                              sizeof(state->back_src),
                                              SETTINGS_PAGE_BACK_X,
                                              SETTINGS_PAGE_BACK_Y,
                                              settings_language_back_clicked) ||
        !settings_language_create_icon_button(screen,
                                              "settings_icon_confirm.png",
                                              state->back_src,
                                              sizeof(state->back_src),
                                              SETTINGS_LANGUAGE_CONFIRM_X,
                                              SETTINGS_LANGUAGE_CONFIRM_Y,
                                              settings_language_confirm_clicked) ||
        !settings_selection_list_create(screen,
                                        &state->list,
                                        settings_language_options,
                                        sizeof(settings_language_options) / sizeof(settings_language_options[0]),
                                        0u,
                                        SETTINGS_SELECTION_LIST_X,
                                        SETTINGS_SELECTION_LIST_Y,
                                        SETTINGS_SELECTION_LIST_VISIBLE_ROWS)) {
        lv_obj_delete(screen);
        free(state->list.rows);
        free(state->list.labels);
        free(state);
        return NULL;
    }

    return screen;
}

void settings_language_page_event(page_manager_page_ctx_t *ctx,
                                  uint32_t code,
                                  uint32_t wparam,
                                  uint32_t lparam)
{
    (void)ctx;
    (void)code;
    (void)wparam;
    (void)lparam;
}
```

- [ ] **Step 7: Run selection-list tests**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py::test_settings_selection_list_reusable_metrics_and_language_options tests/host_unit/test_app_page_manager.py::test_language_page_confirm_and_back_return_to_settings -q
```

Expected: PASS.

### Task 4: Switch Borders to Gray and Verify

**Files:**
- Modify: `app/ui/pages/settings_page.c`
- Modify: `app/ui/pages/home_page.c`
- Test: `tests/host_unit/test_app_page_manager.py`

- [ ] **Step 1: Update settings button border**

In `app/ui/pages/settings_page.c`, replace:

```c
#define SETTINGS_PAGE_BUTTON_BORDER_COLOR 0x43382D
```

with:

```c
#define SETTINGS_PAGE_BUTTON_BORDER_COLOR 0x666666
```

- [ ] **Step 2: Update home user dropdown border**

In `app/ui/pages/home_page.c`, replace:

```c
#define HOME_PAGE_USER_DROPDOWN_BORDER_COLOR 0x3D3734
```

with:

```c
#define HOME_PAGE_USER_DROPDOWN_BORDER_COLOR 0x666666
```

- [ ] **Step 3: Run focused test**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py::test_settings_and_user_borders_are_gray -q
```

Expected: PASS.

- [ ] **Step 4: Run full relevant tests**

Run:

```bash
pytest tests/host_unit/test_app_page_manager.py tests/host_unit/test_app_portable_lvgl_ui.py tests/host_unit/test_ui_style_tiny_ttf.py -q
```

Expected: PASS.

- [ ] **Step 5: Build or run compile-facing tests**

Run:

```bash
pytest tests/host_unit/test_app_portable_lvgl_ui.py -q
```

Expected: PASS. If a local C build target is available and quick, also run the existing host build command from repository docs.

