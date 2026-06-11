# Home User Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Home page top-right user selector and dropdown matching the 800x480 reference layout.

**Architecture:** Keep the feature local to `app/ui/pages/home_page.c` as a small user-switcher section in the existing Home page state. Use platform image path helpers for the avatar resource, LVGL hidden flags for dropdown visibility, and row refresh logic for selected/unselected colors.

**Tech Stack:** C, LVGL 9, existing platform resource helpers, pytest host structural tests, CMake host build.

---

### File Structure

- Modify: `tests/host_unit/test_app_page_manager.py`
  - Add structural tests for the Home page user-switcher constants, LVGL toggle behavior, selected row styles, and resource placement.
- Create: `resources/host/images/avatar_user.png`
  - Copy the provided 48x48 avatar into host image resources with an ASCII filename.
- Modify: `app/ui/pages/home_page.c`
  - Add user-switcher constants, state fields, row callbacks, toggle logic, and creation functions.

### Task 1: Add Failing Structural Tests

**Files:**
- Modify: `tests/host_unit/test_app_page_manager.py`

- [ ] **Step 1: Add user switcher tests**

Append these tests near the existing Home page tests:

```python
def test_home_page_has_reference_positioned_user_switcher():
    home_page = _read("app/ui/pages/home_page.c")

    assert '#define HOME_PAGE_USER_AVATAR_IMAGE_NAME "avatar_user.png"' in home_page
    assert "#define HOME_PAGE_SETTINGS_X 32" in home_page
    assert "#define HOME_PAGE_SETTINGS_Y 24" in home_page
    assert "#define HOME_PAGE_USER_AVATAR_X 677" in home_page
    assert "#define HOME_PAGE_USER_AVATAR_Y 24" in home_page
    assert "#define HOME_PAGE_USER_ARROW_X 749" in home_page
    assert "#define HOME_PAGE_USER_ARROW_Y 43" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_X 399" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_Y 112" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_WIDTH 369" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_HEIGHT 325" in home_page
    assert "#define HOME_PAGE_USER_DROPDOWN_RADIUS 12" in home_page
    assert "home_page_create_user_switcher(state)" in home_page


def test_home_page_user_switcher_toggles_dropdown_and_rows():
    home_page = _read("app/ui/pages/home_page.c")

    assert "lv_obj_add_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN)" in home_page
    assert "lv_obj_clear_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN)" in home_page
    assert "lv_obj_move_foreground(state->user_dropdown)" in home_page
    assert "home_page_toggle_user_dropdown" in home_page
    assert "home_page_user_row_clicked" in home_page
    assert "home_page_refresh_user_rows" in home_page
    assert "state->selected_user_index = 0u" in home_page
    assert "lv_obj_add_event_cb(button, home_page_toggle_user_dropdown, LV_EVENT_CLICKED, state)" in home_page
    assert "lv_obj_add_event_cb(row, home_page_user_row_clicked, LV_EVENT_CLICKED, state)" in home_page


def test_home_page_user_switcher_uses_requested_row_colors_and_resource():
    home_page = _read("app/ui/pages/home_page.c")

    assert "HOME_PAGE_USER_SELECTED_COLOR 0xFFFFFF" in home_page
    assert "HOME_PAGE_USER_UNSELECTED_COLOR 0x2F2B29" in home_page
    assert "ep_platform_lvgl_image_src(HOME_PAGE_USER_AVATAR_IMAGE_NAME" in home_page
    assert 'static const char *const home_page_user_names[HOME_PAGE_USER_COUNT]' in home_page
    assert '"用户1"' in home_page
    assert '"用户4"' in home_page

    assert (REPO_ROOT / "resources/host/images/avatar_user.png").exists()
```

- [ ] **Step 2: Run tests and confirm they fail**

Run:

```bash
pytest -q tests/host_unit/test_app_page_manager.py
```

Expected: the new tests fail because the constants/functions/resource are not implemented yet.

- [ ] **Step 3: Commit is skipped for failing tests**

Keep the failing tests uncommitted until Task 2 and Task 3 make them pass.

### Task 2: Add Avatar Resource

**Files:**
- Create: `resources/host/images/avatar_user.png`

- [ ] **Step 1: Copy the provided avatar into host resources**

Run:

```bash
cp "生成无性别扁平矢量头像-5 1.png" resources/host/images/avatar_user.png
```

- [ ] **Step 2: Verify the resource exists and is 48x48**

Run:

```bash
file resources/host/images/avatar_user.png
```

Expected: output contains `PNG image data, 48 x 48`.

### Task 3: Implement Home User Switcher

**Files:**
- Modify: `app/ui/pages/home_page.c`
- Test: `tests/host_unit/test_app_page_manager.py`
- Resource: `resources/host/images/avatar_user.png`

- [ ] **Step 1: Add constants and state fields**

Add constants near the existing Home page defines:

```c
#define HOME_PAGE_USER_AVATAR_IMAGE_NAME "avatar_user.png"
#define HOME_PAGE_USER_COUNT 4u
#define HOME_PAGE_USER_AVATAR_X 677
#define HOME_PAGE_USER_AVATAR_Y 24
#define HOME_PAGE_USER_AVATAR_SIZE 48
#define HOME_PAGE_USER_ARROW_X 749
#define HOME_PAGE_USER_ARROW_Y 43
#define HOME_PAGE_USER_ARROW_WIDTH 19
#define HOME_PAGE_USER_ARROW_HEIGHT 10
#define HOME_PAGE_USER_DROPDOWN_X 399
#define HOME_PAGE_USER_DROPDOWN_Y 112
#define HOME_PAGE_USER_DROPDOWN_WIDTH 369
#define HOME_PAGE_USER_DROPDOWN_HEIGHT 325
#define HOME_PAGE_USER_DROPDOWN_RADIUS 12
#define HOME_PAGE_USER_ROW_HEIGHT 81
#define HOME_PAGE_USER_SELECTED_COLOR 0xFFFFFF
#define HOME_PAGE_USER_UNSELECTED_COLOR 0x2F2B29
#define HOME_PAGE_USER_DROPDOWN_BORDER_COLOR 0x3D3734
#define HOME_PAGE_USER_TEXT_X 184
#define HOME_PAGE_USER_TEXT_Y 24
#define HOME_PAGE_USER_ROW_AVATAR_X 129
#define HOME_PAGE_USER_ROW_AVATAR_Y 16
```

Update settings coordinates:

```c
#define HOME_PAGE_SETTINGS_X 32
#define HOME_PAGE_SETTINGS_Y 24
```

Add fields to `home_page_state_t`:

```c
char user_avatar_src[128];
lv_obj_t *user_button;
lv_obj_t *user_arrow_button;
lv_obj_t *user_dropdown;
lv_obj_t *user_rows[HOME_PAGE_USER_COUNT];
lv_obj_t *user_row_labels[HOME_PAGE_USER_COUNT];
size_t selected_user_index;
bool user_dropdown_visible;
```

- [ ] **Step 2: Add helper functions**

Add helpers after `home_page_create_settings_button`:

```c
static const char *const home_page_user_names[HOME_PAGE_USER_COUNT] = {
    "用户1",
    "用户2",
    "用户3",
    "用户4",
};

static void home_page_set_clean_clickable_style(lv_obj_t *obj)
{
    if (obj == NULL) {
        return;
    }

    lv_obj_remove_style_all(obj);
    lv_obj_set_style_bg_opa(obj, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(obj, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(obj, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(obj, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(obj, LV_OBJ_FLAG_CLICKABLE);
}

static void home_page_set_user_dropdown_visible(home_page_state_t *state, bool visible)
{
    if (state == NULL || state->user_dropdown == NULL) {
        return;
    }

    state->user_dropdown_visible = visible;
    if (visible) {
        lv_obj_clear_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN);
        lv_obj_move_foreground(state->user_dropdown);
    } else {
        lv_obj_add_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN);
    }
}

static void home_page_toggle_user_dropdown(lv_event_t *event)
{
    home_page_state_t *state;

    state = (home_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL) {
        return;
    }

    home_page_set_user_dropdown_visible(state, !state->user_dropdown_visible);
}
```

- [ ] **Step 3: Add row refresh and click behavior**

Add:

```c
static void home_page_refresh_user_rows(home_page_state_t *state)
{
    for (size_t i = 0u; i < HOME_PAGE_USER_COUNT; ++i) {
        bool selected;
        lv_color_t bg_color;
        lv_color_t text_color;

        selected = i == state->selected_user_index;
        bg_color = lv_color_hex(selected ? HOME_PAGE_USER_SELECTED_COLOR : HOME_PAGE_USER_UNSELECTED_COLOR);
        text_color = selected ? lv_color_black() : lv_color_white();

        if (state->user_rows[i] != NULL) {
            lv_obj_set_style_bg_color(state->user_rows[i], bg_color, LV_PART_MAIN);
            lv_obj_set_style_bg_opa(state->user_rows[i], LV_OPA_COVER, LV_PART_MAIN);
        }

        if (state->user_row_labels[i] != NULL) {
            lv_obj_set_style_text_color(state->user_row_labels[i], text_color, LV_PART_MAIN);
        }
    }
}

static void home_page_user_row_clicked(lv_event_t *event)
{
    home_page_state_t *state;
    lv_obj_t *row;

    state = (home_page_state_t *)lv_event_get_user_data(event);
    row = (lv_obj_t *)lv_event_get_target(event);
    if (state == NULL || row == NULL) {
        return;
    }

    for (size_t i = 0u; i < HOME_PAGE_USER_COUNT; ++i) {
        if (state->user_rows[i] == row) {
            state->selected_user_index = i;
            home_page_refresh_user_rows(state);
            home_page_set_user_dropdown_visible(state, false);
            return;
        }
    }
}
```

- [ ] **Step 4: Add creation functions**

Add:

```c
static void home_page_add_user_avatar(lv_obj_t *parent, const char *src)
{
    lv_obj_t *avatar;
    lv_obj_t *fallback;

    if (parent == NULL) {
        return;
    }

    if (src != NULL && src[0] != '\0') {
        avatar = lv_image_create(parent);
        if (avatar != NULL) {
            lv_image_set_src(avatar, src);
            lv_obj_set_pos(avatar, 0, 0);
            return;
        }
    }

    fallback = lv_label_create(parent);
    if (fallback != NULL) {
        lv_label_set_text(fallback, "U");
        lv_obj_set_style_text_color(fallback, lv_color_white(), LV_PART_MAIN);
        lv_obj_center(fallback);
    }
}

static void home_page_create_user_dropdown(home_page_state_t *state)
{
    lv_obj_t *row;
    lv_obj_t *avatar_holder;
    lv_obj_t *label;

    state->user_dropdown = lv_obj_create(state->screen);
    if (state->user_dropdown == NULL) {
        return;
    }

    lv_obj_remove_style_all(state->user_dropdown);
    lv_obj_set_pos(state->user_dropdown, HOME_PAGE_USER_DROPDOWN_X, HOME_PAGE_USER_DROPDOWN_Y);
    lv_obj_set_size(state->user_dropdown, HOME_PAGE_USER_DROPDOWN_WIDTH, HOME_PAGE_USER_DROPDOWN_HEIGHT);
    lv_obj_set_style_radius(state->user_dropdown, HOME_PAGE_USER_DROPDOWN_RADIUS, LV_PART_MAIN);
    lv_obj_set_style_bg_color(state->user_dropdown, lv_color_hex(HOME_PAGE_USER_UNSELECTED_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(state->user_dropdown, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_color(state->user_dropdown, lv_color_hex(HOME_PAGE_USER_DROPDOWN_BORDER_COLOR), LV_PART_MAIN);
    lv_obj_set_style_border_width(state->user_dropdown, 1, LV_PART_MAIN);
    lv_obj_set_style_clip_corner(state->user_dropdown, true, LV_PART_MAIN);
    lv_obj_clear_flag(state->user_dropdown, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN);

    for (size_t i = 0u; i < HOME_PAGE_USER_COUNT; ++i) {
        row = lv_obj_create(state->user_dropdown);
        if (row == NULL) {
            continue;
        }

        state->user_rows[i] = row;
        lv_obj_remove_style_all(row);
        lv_obj_set_pos(row, 0, (int32_t)i * HOME_PAGE_USER_ROW_HEIGHT);
        lv_obj_set_size(row, HOME_PAGE_USER_DROPDOWN_WIDTH,
                        i == HOME_PAGE_USER_COUNT - 1u ? 82 : HOME_PAGE_USER_ROW_HEIGHT);
        lv_obj_set_style_radius(row, 0, LV_PART_MAIN);
        lv_obj_set_style_border_width(row, 0, LV_PART_MAIN);
        lv_obj_clear_flag(row, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(row, home_page_user_row_clicked, LV_EVENT_CLICKED, state);

        avatar_holder = lv_obj_create(row);
        if (avatar_holder != NULL) {
            home_page_set_clean_clickable_style(avatar_holder);
            lv_obj_set_pos(avatar_holder, HOME_PAGE_USER_ROW_AVATAR_X, HOME_PAGE_USER_ROW_AVATAR_Y);
            lv_obj_set_size(avatar_holder, HOME_PAGE_USER_AVATAR_SIZE, HOME_PAGE_USER_AVATAR_SIZE);
            home_page_add_user_avatar(avatar_holder, state->user_avatar_src);
        }

        label = lv_label_create(row);
        if (label != NULL) {
            state->user_row_labels[i] = label;
            lv_label_set_text(label, home_page_user_names[i]);
            lv_obj_set_pos(label, HOME_PAGE_USER_TEXT_X, HOME_PAGE_USER_TEXT_Y);
        }
    }

    home_page_refresh_user_rows(state);
}

static void home_page_create_user_switcher(home_page_state_t *state)
{
    lv_obj_t *button;
    lv_obj_t *arrow;

    if (state == NULL || state->screen == NULL) {
        return;
    }

    state->selected_user_index = 0u;
    (void)ep_platform_lvgl_image_src(HOME_PAGE_USER_AVATAR_IMAGE_NAME,
                                     state->user_avatar_src,
                                     sizeof(state->user_avatar_src));

    button = lv_button_create(state->screen);
    state->user_button = button;
    if (button != NULL) {
        home_page_set_clean_clickable_style(button);
        lv_obj_set_pos(button, HOME_PAGE_USER_AVATAR_X, HOME_PAGE_USER_AVATAR_Y);
        lv_obj_set_size(button, HOME_PAGE_USER_AVATAR_SIZE, HOME_PAGE_USER_AVATAR_SIZE);
        lv_obj_add_event_cb(button, home_page_toggle_user_dropdown, LV_EVENT_CLICKED, state);
        home_page_add_user_avatar(button, state->user_avatar_src);
    }

    arrow = lv_button_create(state->screen);
    state->user_arrow_button = arrow;
    if (arrow != NULL) {
        lv_obj_t *label;

        home_page_set_clean_clickable_style(arrow);
        lv_obj_set_pos(arrow, HOME_PAGE_USER_ARROW_X, HOME_PAGE_USER_ARROW_Y);
        lv_obj_set_size(arrow, HOME_PAGE_USER_ARROW_WIDTH, HOME_PAGE_USER_ARROW_HEIGHT);
        lv_obj_add_event_cb(arrow, home_page_toggle_user_dropdown, LV_EVENT_CLICKED, state);

        label = lv_label_create(arrow);
        if (label != NULL) {
            lv_label_set_text(label, "⌄");
            lv_obj_set_style_text_color(label, lv_color_white(), LV_PART_MAIN);
            lv_obj_center(label);
        }
    }

    home_page_create_user_dropdown(state);
}
```

- [ ] **Step 5: Wire creation into Home page**

Call the switcher after the settings button and after carousel creation if foreground ordering needs the dropdown above carousel:

```c
home_page_create_settings_button(state);
home_page_create_carousel(state);
home_page_create_user_switcher(state);
```

- [ ] **Step 6: Run focused tests**

Run:

```bash
pytest -q tests/host_unit/test_app_page_manager.py
```

Expected: all tests in this file pass.

- [ ] **Step 7: Build host app**

Run:

```bash
cmake --build build --target ep_host_app
```

Expected: build succeeds.

- [ ] **Step 8: Commit implementation**

Run:

```bash
git add app/ui/pages/home_page.c tests/host_unit/test_app_page_manager.py resources/host/images/avatar_user.png
git commit -m "feat: add home user switcher"
```

Expected: commit succeeds and excludes root reference images and the luban-lite submodule change.
