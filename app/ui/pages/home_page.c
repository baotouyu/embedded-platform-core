#include "pages/home_page.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "ep_simple_recipe.h"
#include "lvgl.h"
#include "pages/app_pages.h"
#include "ui_style.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define HOME_PAGE_EVENT_REFRESH 1u

#define HOME_PAGE_BG_IMAGE_NAME "home_bg.png"
#define HOME_PAGE_SETTINGS_ICON_NAME "icon_settings.png"
#define HOME_PAGE_USER_AVATAR_1_IMAGE_NAME "avatar_user_1.png"
#define HOME_PAGE_USER_AVATAR_2_IMAGE_NAME "avatar_user_2.png"
#define HOME_PAGE_USER_AVATAR_3_IMAGE_NAME "avatar_user_3.png"
#define HOME_PAGE_USER_AVATAR_4_IMAGE_NAME "avatar_user_4.png"
#define HOME_PAGE_SETTINGS_TEXT "Settings"
#define HOME_PAGE_RECIPE_DB_NAME "recipelib.db"
#define HOME_PAGE_MAX_RECIPES 16u
#define HOME_PAGE_USER_COUNT 4u
#define HOME_PAGE_CAROUSEL_SLOT_COUNT 5u
#define HOME_PAGE_FAR_LEFT_SLOT 0u
#define HOME_PAGE_LEFT_SLOT 1u
#define HOME_PAGE_CENTER_SLOT 2u
#define HOME_PAGE_RIGHT_SLOT 3u
#define HOME_PAGE_FAR_RIGHT_SLOT 4u
#define HOME_PAGE_SWIPE_THRESHOLD 80
#define HOME_PAGE_WEIGHT_UNIT 1024
#define HOME_PAGE_SNAP_ANIM_MS 120u
#define HOME_PAGE_SNAP_EXTRA_STEP_MS 45u
#define HOME_PAGE_SNAP_TIMER_PERIOD_MS 16u
#define HOME_PAGE_DISTANCE_SNAP_THRESHOLD 14
#define HOME_PAGE_RELEASE_VELOCITY_THRESHOLD 160
#define HOME_PAGE_FAST_RELEASE_VELOCITY_THRESHOLD 420
#define HOME_PAGE_FLING_RELEASE_VELOCITY_THRESHOLD 760
#define HOME_PAGE_MAX_INERTIA_STEPS 3
#define HOME_PAGE_MIN_VELOCITY_SAMPLE_DELTA 2
#define HOME_PAGE_SCREEN_WIDTH 800
#define HOME_PAGE_SCREEN_HEIGHT 480
#define HOME_PAGE_HEADER_HEIGHT 96
#define HOME_PAGE_MENU_HEIGHT 260
#define HOME_PAGE_TITLE_HEIGHT 124
#define HOME_PAGE_SIDE_ITEM_SIZE 180
#define HOME_PAGE_CENTER_ITEM_SIZE 260
#define HOME_PAGE_RECIPE_IMAGE_NATIVE_SIZE 240
#define HOME_PAGE_SELECTED_SCALE ((HOME_PAGE_CENTER_ITEM_SIZE * 256) / HOME_PAGE_RECIPE_IMAGE_NATIVE_SIZE)
#define HOME_PAGE_SIDE_SCALE ((HOME_PAGE_SIDE_ITEM_SIZE * 256) / HOME_PAGE_RECIPE_IMAGE_NATIVE_SIZE)
#define HOME_PAGE_SIDE_SLOT_WIDTH 270
#define HOME_PAGE_CENTER_SLOT_WIDTH 260
#define HOME_PAGE_FAR_LEFT_SLOT_X (-270)
#define HOME_PAGE_LEFT_SLOT_X 0
#define HOME_PAGE_CENTER_SLOT_X 270
#define HOME_PAGE_RIGHT_SLOT_X 530
#define HOME_PAGE_FAR_RIGHT_SLOT_X 800
#define HOME_PAGE_MENU_Y HOME_PAGE_HEADER_HEIGHT
#define HOME_PAGE_SLOT_Y 0
#define HOME_PAGE_LEFT_IMAGE_X 42
#define HOME_PAGE_RIGHT_IMAGE_X 48
#define HOME_PAGE_SIDE_IMAGE_Y 40
#define HOME_PAGE_CENTER_IMAGE_X 0
#define HOME_PAGE_CENTER_IMAGE_Y 0
#define HOME_PAGE_TITLE_Y 268
#define HOME_PAGE_LEFT_TITLE_X 0
#define HOME_PAGE_CENTER_TITLE_X 0
#define HOME_PAGE_RIGHT_TITLE_X 10
#define HOME_PAGE_SETTINGS_X 32
#define HOME_PAGE_SETTINGS_Y 24
#define HOME_PAGE_SETTINGS_SIZE 48
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
#define HOME_PAGE_USER_DROPDOWN_BORDER_COLOR 0x666666
#define HOME_PAGE_USER_ROW_BORDER_COLOR 0x666666
#define HOME_PAGE_USER_ROW_CONTENT_WIDTH 138
#define HOME_PAGE_USER_ROW_CONTENT_HEIGHT HOME_PAGE_USER_AVATAR_SIZE
#define HOME_PAGE_USER_ROW_CONTENT_X ((HOME_PAGE_USER_DROPDOWN_WIDTH - HOME_PAGE_USER_ROW_CONTENT_WIDTH) / 2)
#define HOME_PAGE_USER_ROW_CONTENT_Y 16
#define HOME_PAGE_USER_ROW_AVATAR_Y 0
#define HOME_PAGE_USER_LABEL_X 66
#define HOME_PAGE_USER_LABEL_Y 10
#define HOME_PAGE_USER_LABEL_WIDTH 72
#define HOME_PAGE_USER_LABEL_HEIGHT 32

typedef struct {
    lv_obj_t *container;
    lv_obj_t *image;
    lv_obj_t *label;
    int32_t base_x;
    int32_t base_y;
    int32_t width;
    int32_t side_image_x;
    int32_t title_x;
    size_t recipe_index;
    int32_t drag_weight;
    bool has_recipe;
    bool is_center;
} home_page_carousel_slot_t;

typedef struct {
    ep_simple_recipe_item_t recipes[HOME_PAGE_MAX_RECIPES];
    char bg_src[128];
    char settings_src[128];
    char user_avatar_src[HOME_PAGE_USER_COUNT][128];
    char recipe_src[HOME_PAGE_CAROUSEL_SLOT_COUNT][160];
    size_t recipe_count;
    size_t selected_index;
    lv_obj_t *screen;
    lv_obj_t *carousel;
    lv_obj_t *user_button;
    lv_obj_t *user_avatar_image;
    lv_obj_t *user_arrow_button;
    lv_obj_t *user_dropdown_mask;
    lv_obj_t *user_dropdown;
    lv_obj_t *user_rows[HOME_PAGE_USER_COUNT];
    lv_obj_t *user_row_content[HOME_PAGE_USER_COUNT];
    lv_obj_t *user_row_avatar_holders[HOME_PAGE_USER_COUNT];
    lv_obj_t *user_row_labels[HOME_PAGE_USER_COUNT];
    home_page_carousel_slot_t slots[HOME_PAGE_CAROUSEL_SLOT_COUNT];
    lv_timer_t *snap_timer;
    uint32_t snap_start_tick;
    int32_t snap_start_offset;
    int32_t snap_target_offset;
    int32_t snap_target_step;
    int32_t snap_total_steps;
    int32_t snap_completed_steps;
    int32_t snap_step_direction;
    int32_t snap_start_progress;
    int32_t snap_target_progress;
    uint32_t snap_duration_ms;
    bool dragging;
    int32_t drag_start_x;
    int32_t drag_base_offset;
    int32_t last_drag_x;
    uint32_t last_drag_tick;
    int32_t release_velocity;
    int32_t drag_offset;
    size_t selected_user_index;
    bool user_dropdown_visible;
} home_page_state_t;

static const char *const home_page_user_names[HOME_PAGE_USER_COUNT] = {
    "用户1",
    "用户2",
    "用户3",
    "用户4",
};

static const char *const home_page_user_avatar_names[HOME_PAGE_USER_COUNT] = {
    HOME_PAGE_USER_AVATAR_1_IMAGE_NAME,
    HOME_PAGE_USER_AVATAR_2_IMAGE_NAME,
    HOME_PAGE_USER_AVATAR_3_IMAGE_NAME,
    HOME_PAGE_USER_AVATAR_4_IMAGE_NAME,
};

static const lv_point_precise_t home_page_user_arrow_points[] = {
    {0, 0},
    {9, 8},
    {18, 0},
};

static int home_page_wrap_index(int index, size_t count)
{
    int count_i;

    if (count == 0u) {
        return 0;
    }

    count_i = (int)count;
    while (index < 0) {
        index += count_i;
    }

    return index % count_i;
}

static const char *home_page_extract_url_filename(const char *url)
{
    const char *cursor;
    const char *filename;

    if (url == NULL || url[0] == '\0') {
        return "";
    }

    filename = url;
    cursor = url;
    while (*cursor != '\0') {
        if (*cursor == '/') {
            filename = cursor + 1;
        }
        cursor++;
    }

    return filename;
}

static int home_page_lvgl_recipe_src(
    const ep_simple_recipe_item_t *recipe,
    char *buffer,
    size_t buffer_size)
{
    const char *filename;

    if (recipe == NULL || buffer == NULL || buffer_size == 0u) {
        return EP_ERR_INVAL;
    }

    filename = home_page_extract_url_filename(recipe->portrait_image_url);
    if (filename[0] == '\0') {
        buffer[0] = '\0';
        return EP_ERR_INVAL;
    }

    return ep_platform_lvgl_recipe_src(filename, buffer, buffer_size);
}

static void home_page_style_screen(home_page_state_t *state)
{
    lv_obj_t *bg;

    if (state == NULL || state->screen == NULL) {
        return;
    }

    lv_obj_remove_style_all(state->screen);
    lv_obj_set_style_bg_color(state->screen, lv_color_hex(0x000000), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(state->screen, LV_OPA_COVER, LV_PART_MAIN);

    if (ep_platform_lvgl_image_src(HOME_PAGE_BG_IMAGE_NAME, state->bg_src, sizeof(state->bg_src)) != EP_OK) {
        return;
    }

    bg = lv_image_create(state->screen);
    if (bg == NULL) {
        return;
    }

    lv_image_set_src(bg, state->bg_src);
    lv_obj_set_size(bg, HOME_PAGE_SCREEN_WIDTH, HOME_PAGE_SCREEN_HEIGHT);
    lv_obj_set_pos(bg, 0, 0);
    lv_obj_move_background(bg);
}

static void home_page_settings_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_switch(APP_PAGE_SETTINGS, LV_SCR_LOAD_ANIM_MOVE_LEFT, 180, true);
}

static void home_page_create_settings_button(home_page_state_t *state)
{
    lv_obj_t *screen;
    lv_obj_t *button;
    lv_obj_t *icon;
    lv_obj_t *fallback;

    if (state == NULL || state->screen == NULL) {
        return;
    }

    screen = state->screen;
    button = lv_button_create(screen);
    if (button == NULL) {
        return;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, HOME_PAGE_SETTINGS_SIZE, HOME_PAGE_SETTINGS_SIZE);
    lv_obj_set_pos(button, HOME_PAGE_SETTINGS_X, HOME_PAGE_SETTINGS_Y);
    lv_obj_set_style_bg_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_event_cb(button, home_page_settings_clicked, LV_EVENT_CLICKED, NULL);

    if (ep_platform_lvgl_image_src(HOME_PAGE_SETTINGS_ICON_NAME, state->settings_src, sizeof(state->settings_src)) == EP_OK) {
        icon = lv_image_create(button);
        if (icon != NULL) {
            lv_image_set_src(icon, state->settings_src);
            lv_obj_set_pos(icon, 0, 0);
            return;
        }
    }

    fallback = lv_label_create(button);
    if (fallback != NULL) {
        lv_label_set_text(fallback, HOME_PAGE_SETTINGS_TEXT);
        lv_obj_set_style_text_color(fallback, lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_text_font(fallback, ui_style_font(UI_STYLE_FONT_HOME_SIDE), LV_PART_MAIN);
        lv_obj_center(fallback);
    }
}

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
        if (state->user_dropdown_mask != NULL) {
            lv_obj_clear_flag(state->user_dropdown_mask, LV_OBJ_FLAG_HIDDEN);
            lv_obj_move_foreground(state->user_dropdown_mask);
        }
        lv_obj_clear_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN);
        lv_obj_move_foreground(state->user_dropdown);
    } else {
        if (state->user_dropdown_mask != NULL) {
            lv_obj_add_flag(state->user_dropdown_mask, LV_OBJ_FLAG_HIDDEN);
        }
        lv_obj_add_flag(state->user_dropdown, LV_OBJ_FLAG_HIDDEN);
    }
}

static void home_page_user_mask_clicked(lv_event_t *event)
{
    home_page_state_t *state;

    state = (home_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL) {
        return;
    }

    home_page_set_user_dropdown_visible(state, false);
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

static void home_page_refresh_user_rows(home_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

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

static void home_page_refresh_selected_user_avatar(home_page_state_t *state);

static void home_page_user_row_clicked(lv_event_t *event)
{
    home_page_state_t *state;
    lv_obj_t *target;

    state = (home_page_state_t *)lv_event_get_user_data(event);
    target = lv_event_get_current_target_obj(event);
    if (state == NULL || target == NULL) {
        return;
    }

    for (size_t i = 0u; i < HOME_PAGE_USER_COUNT; ++i) {
        if (state->user_rows[i] == target ||
            state->user_row_content[i] == target ||
            state->user_row_avatar_holders[i] == target ||
            state->user_row_labels[i] == target) {
            state->selected_user_index = i;
            home_page_refresh_user_rows(state);
            home_page_refresh_selected_user_avatar(state);
            home_page_set_user_dropdown_visible(state, false);
            return;
        }
    }
}

static lv_obj_t *home_page_add_user_avatar(lv_obj_t *parent, const char *src)
{
    lv_obj_t *avatar;
    lv_obj_t *fallback;

    if (parent == NULL) {
        return NULL;
    }

    if (src != NULL && src[0] != '\0') {
        avatar = lv_image_create(parent);
        if (avatar != NULL) {
            lv_image_set_src(avatar, src);
            lv_obj_set_pos(avatar, 0, 0);
            return avatar;
        }
    }

    fallback = lv_label_create(parent);
    if (fallback != NULL) {
        lv_label_set_text(fallback, "U");
        lv_obj_set_style_text_color(fallback, lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_text_font(fallback, ui_style_font(UI_STYLE_FONT_HOME_USER), LV_PART_MAIN);
        lv_obj_center(fallback);
    }
    return NULL;
}

static void home_page_refresh_selected_user_avatar(home_page_state_t *state)
{
    if (state == NULL ||
        state->user_avatar_image == NULL ||
        state->selected_user_index >= HOME_PAGE_USER_COUNT ||
        state->user_avatar_src[state->selected_user_index][0] == '\0') {
        return;
    }

    lv_image_set_src(state->user_avatar_image, state->user_avatar_src[state->selected_user_index]);
}

static void home_page_create_user_dropdown(home_page_state_t *state)
{
    lv_obj_t *row;
    lv_obj_t *content;
    lv_obj_t *avatar_holder;
    lv_obj_t *label;

    if (state == NULL || state->screen == NULL) {
        return;
    }

    state->user_dropdown_mask = lv_obj_create(state->screen);
    if (state->user_dropdown_mask != NULL) {
        lv_obj_remove_style_all(state->user_dropdown_mask);
        lv_obj_set_pos(state->user_dropdown_mask, 0, 0);
        lv_obj_set_size(state->user_dropdown_mask, HOME_PAGE_SCREEN_WIDTH, HOME_PAGE_SCREEN_HEIGHT);
        lv_obj_set_style_bg_opa(state->user_dropdown_mask, LV_OPA_TRANSP, LV_PART_MAIN);
        lv_obj_set_style_border_opa(state->user_dropdown_mask, LV_OPA_TRANSP, LV_PART_MAIN);
        lv_obj_set_style_shadow_opa(state->user_dropdown_mask, LV_OPA_TRANSP, LV_PART_MAIN);
        lv_obj_clear_flag(state->user_dropdown_mask, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(state->user_dropdown_mask, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_flag(state->user_dropdown_mask, LV_OBJ_FLAG_HIDDEN);
        lv_obj_add_event_cb(state->user_dropdown_mask, home_page_user_mask_clicked, LV_EVENT_CLICKED, state);
    }

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
        lv_obj_set_size(row,
                        HOME_PAGE_USER_DROPDOWN_WIDTH,
                        i == HOME_PAGE_USER_COUNT - 1u ? 82 : HOME_PAGE_USER_ROW_HEIGHT);
        lv_obj_set_style_radius(row, 0, LV_PART_MAIN);
        lv_obj_set_style_border_width(row, i == HOME_PAGE_USER_COUNT - 1u ? 0 : 1, LV_PART_MAIN);
        lv_obj_set_style_border_side(row, LV_BORDER_SIDE_BOTTOM, LV_PART_MAIN);
        lv_obj_set_style_border_color(row, lv_color_hex(HOME_PAGE_USER_ROW_BORDER_COLOR), LV_PART_MAIN);
        lv_obj_clear_flag(row, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(row, home_page_user_row_clicked, LV_EVENT_CLICKED, state);

        content = lv_obj_create(row);
        if (content == NULL) {
            continue;
        }

        state->user_row_content[i] = content;
        home_page_set_clean_clickable_style(content);
        lv_obj_set_pos(content, HOME_PAGE_USER_ROW_CONTENT_X, HOME_PAGE_USER_ROW_CONTENT_Y);
        lv_obj_set_size(content, HOME_PAGE_USER_ROW_CONTENT_WIDTH, HOME_PAGE_USER_ROW_CONTENT_HEIGHT);
        lv_obj_add_event_cb(content, home_page_user_row_clicked, LV_EVENT_CLICKED, state);

        avatar_holder = lv_obj_create(content);
        if (avatar_holder != NULL) {
            state->user_row_avatar_holders[i] = avatar_holder;
            home_page_set_clean_clickable_style(avatar_holder);
            lv_obj_set_pos(avatar_holder, 0, HOME_PAGE_USER_ROW_AVATAR_Y);
            lv_obj_set_size(avatar_holder, HOME_PAGE_USER_AVATAR_SIZE, HOME_PAGE_USER_AVATAR_SIZE);
            lv_obj_add_event_cb(avatar_holder, home_page_user_row_clicked, LV_EVENT_CLICKED, state);
            home_page_add_user_avatar(avatar_holder, state->user_avatar_src[i]);
        }

        label = lv_label_create(content);
        if (label != NULL) {
            state->user_row_labels[i] = label;
            lv_obj_remove_style_all(label);
            lv_obj_set_size(label, HOME_PAGE_USER_LABEL_WIDTH, HOME_PAGE_USER_LABEL_HEIGHT);
            lv_obj_set_pos(label, HOME_PAGE_USER_LABEL_X, HOME_PAGE_USER_LABEL_Y);
            lv_label_set_text(label, home_page_user_names[i]);
            lv_obj_set_style_text_font(label, ui_style_font(UI_STYLE_FONT_HOME_SIDE), LV_PART_MAIN);
            lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_LEFT, LV_PART_MAIN);
            lv_obj_add_flag(label, LV_OBJ_FLAG_CLICKABLE);
            lv_obj_add_event_cb(label, home_page_user_row_clicked, LV_EVENT_CLICKED, state);
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
    for (size_t i = 0u; i < HOME_PAGE_USER_COUNT; ++i) {
        (void)ep_platform_lvgl_image_src(home_page_user_avatar_names[i],
                                         state->user_avatar_src[i],
                                         sizeof(state->user_avatar_src[i]));
    }

    button = lv_button_create(state->screen);
    state->user_button = button;
    if (button != NULL) {
        home_page_set_clean_clickable_style(button);
        lv_obj_set_pos(button, HOME_PAGE_USER_AVATAR_X, HOME_PAGE_USER_AVATAR_Y);
        lv_obj_set_size(button, HOME_PAGE_USER_AVATAR_SIZE, HOME_PAGE_USER_AVATAR_SIZE);
        lv_obj_add_event_cb(button, home_page_toggle_user_dropdown, LV_EVENT_CLICKED, state);
        state->user_avatar_image = home_page_add_user_avatar(button, state->user_avatar_src[state->selected_user_index]);
    }

    arrow = lv_button_create(state->screen);
    state->user_arrow_button = arrow;
    if (arrow != NULL) {
        lv_obj_t *arrow_line;

        home_page_set_clean_clickable_style(arrow);
        lv_obj_set_pos(arrow, HOME_PAGE_USER_ARROW_X, HOME_PAGE_USER_ARROW_Y);
        lv_obj_set_size(arrow, HOME_PAGE_USER_ARROW_WIDTH, HOME_PAGE_USER_ARROW_HEIGHT);
        lv_obj_add_event_cb(arrow, home_page_toggle_user_dropdown, LV_EVENT_CLICKED, state);

        arrow_line = lv_line_create(arrow);
        if (arrow_line != NULL) {
            lv_line_set_points(arrow_line,
                               home_page_user_arrow_points,
                               sizeof(home_page_user_arrow_points) / sizeof(home_page_user_arrow_points[0]));
            lv_obj_set_style_line_color(arrow_line, lv_color_white(), LV_PART_MAIN);
            lv_obj_set_style_line_width(arrow_line, 2, LV_PART_MAIN);
            lv_obj_set_style_line_rounded(arrow_line, true, LV_PART_MAIN);
            lv_obj_set_pos(arrow_line, 0, 1);
        }
    }

    home_page_create_user_dropdown(state);
}

static int home_page_load_recipes(home_page_state_t *state)
{
    ep_simple_recipe_store_t *store = NULL;
    char recipe_db_path[160];
    size_t count = 0u;
    int rc;

    rc = ep_platform_recipe_path(HOME_PAGE_RECIPE_DB_NAME, recipe_db_path, sizeof(recipe_db_path));
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_simple_recipe_open_saas2_db(recipe_db_path, &store);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_simple_recipe_load_list(
        store,
        state->recipes,
        HOME_PAGE_MAX_RECIPES,
        &count);
    ep_simple_recipe_close(store);
    if (rc != EP_OK && rc != EP_ERR_BUSY) {
        return rc;
    }

    state->recipe_count = count;
    state->selected_index = count > 0u ? count / 2u : 0u;
    return count > 0u ? EP_OK : EP_ERR_INVAL;
}

static void home_page_set_slot_recipe(
    home_page_state_t *state,
    size_t slot_index,
    size_t recipe_index)
{
    home_page_carousel_slot_t *slot;
    ep_simple_recipe_item_t *recipe;

    if (slot_index >= HOME_PAGE_CAROUSEL_SLOT_COUNT || state->recipe_count == 0u) {
        return;
    }

    slot = &state->slots[slot_index];
    recipe = &state->recipes[recipe_index];

    if (slot->has_recipe && slot->recipe_index == recipe_index) {
        return;
    }

    if (slot->image != NULL &&
        home_page_lvgl_recipe_src(recipe, state->recipe_src[slot_index], sizeof(state->recipe_src[slot_index])) == EP_OK) {
        lv_image_set_src(slot->image, state->recipe_src[slot_index]);
    }

    if (slot->label != NULL) {
        lv_label_set_text(slot->label, recipe->name);
    }

    slot->recipe_index = recipe_index;
    slot->has_recipe = true;
}

static int32_t home_page_abs_i32(int32_t value)
{
    return value < 0 ? -value : value;
}

static int32_t home_page_clamp_i32(int32_t value, int32_t min_value, int32_t max_value)
{
    if (value < min_value) {
        return min_value;
    }

    if (value > max_value) {
        return max_value;
    }

    return value;
}

static int32_t home_page_lerp_i32(int32_t start, int32_t end, int32_t progress)
{
    return start + ((end - start) * progress / HOME_PAGE_WEIGHT_UNIT);
}

static int32_t home_page_visual_progress_for_offset(int32_t drag_offset)
{
    return drag_offset * HOME_PAGE_WEIGHT_UNIT / HOME_PAGE_SWIPE_THRESHOLD;
}

static int32_t home_page_lerp_progress_i32(int32_t start, int32_t end, int32_t progress, int32_t max_progress)
{
    return start + ((end - start) * progress / max_progress);
}

static int32_t home_page_ease_out_quad(int32_t progress, int32_t max_progress)
{
    int32_t inverse;

    progress = home_page_clamp_i32(progress, 0, max_progress);
    inverse = max_progress - progress;
    return max_progress - (inverse * inverse / max_progress);
}

static int32_t home_page_abs_weight(int32_t visual_weight)
{
    return home_page_abs_i32(visual_weight);
}

static int32_t home_page_visual_x_for_weight(int32_t visual_weight)
{
    if (visual_weight <= -HOME_PAGE_WEIGHT_UNIT) {
        return HOME_PAGE_LEFT_SLOT_X +
            ((visual_weight + HOME_PAGE_WEIGHT_UNIT) * (HOME_PAGE_LEFT_SLOT_X - HOME_PAGE_FAR_LEFT_SLOT_X) /
             HOME_PAGE_WEIGHT_UNIT);
    }

    if (visual_weight <= 0) {
        return HOME_PAGE_CENTER_SLOT_X +
            (visual_weight * (HOME_PAGE_CENTER_SLOT_X - HOME_PAGE_LEFT_SLOT_X) / HOME_PAGE_WEIGHT_UNIT);
    }

    if (visual_weight <= HOME_PAGE_WEIGHT_UNIT) {
        return HOME_PAGE_CENTER_SLOT_X +
            (visual_weight * (HOME_PAGE_RIGHT_SLOT_X - HOME_PAGE_CENTER_SLOT_X) / HOME_PAGE_WEIGHT_UNIT);
    }

    return HOME_PAGE_RIGHT_SLOT_X +
        ((visual_weight - HOME_PAGE_WEIGHT_UNIT) * (HOME_PAGE_FAR_RIGHT_SLOT_X - HOME_PAGE_RIGHT_SLOT_X) /
         HOME_PAGE_WEIGHT_UNIT);
}

static int32_t home_page_image_x_for_weight(int32_t visual_weight)
{
    if (visual_weight < -HOME_PAGE_WEIGHT_UNIT) {
        return HOME_PAGE_LEFT_IMAGE_X;
    }

    if (visual_weight < 0) {
        return home_page_lerp_i32(HOME_PAGE_CENTER_IMAGE_X,
                                  HOME_PAGE_LEFT_IMAGE_X,
                                  -visual_weight);
    }

    if (visual_weight <= HOME_PAGE_WEIGHT_UNIT) {
        return home_page_lerp_i32(HOME_PAGE_CENTER_IMAGE_X,
                                  HOME_PAGE_RIGHT_IMAGE_X,
                                  visual_weight);
    }

    return HOME_PAGE_RIGHT_IMAGE_X;
}

static int32_t home_page_image_y_for_weight(int32_t visual_weight)
{
    int32_t progress;

    progress = home_page_clamp_i32(home_page_abs_weight(visual_weight), 0, HOME_PAGE_WEIGHT_UNIT);
    return home_page_lerp_i32(HOME_PAGE_CENTER_IMAGE_Y, HOME_PAGE_SIDE_IMAGE_Y, progress);
}

static int32_t home_page_scale_for_weight(int32_t visual_weight)
{
    int32_t progress;

    progress = home_page_clamp_i32(home_page_abs_weight(visual_weight), 0, HOME_PAGE_WEIGHT_UNIT);
    return home_page_lerp_i32(HOME_PAGE_SELECTED_SCALE, HOME_PAGE_SIDE_SCALE, progress);
}

static lv_opa_t home_page_opa_for_weight(int32_t visual_weight)
{
    int32_t progress;

    progress = home_page_clamp_i32(home_page_abs_weight(visual_weight), 0, HOME_PAGE_WEIGHT_UNIT);
    return (lv_opa_t)home_page_lerp_i32(LV_OPA_COVER, 205, progress);
}

static void home_page_apply_slot_transform(
    home_page_carousel_slot_t *slot,
    int32_t drag_offset)
{
    int32_t x;
    int32_t visual_progress;
    int32_t visual_weight;
    int32_t scale;
    int32_t image_x;
    int32_t image_y;
    lv_opa_t opa;

    visual_progress = home_page_visual_progress_for_offset(drag_offset);
    visual_weight = slot->drag_weight * HOME_PAGE_WEIGHT_UNIT + visual_progress;
    x = home_page_visual_x_for_weight(visual_weight);
    scale = home_page_scale_for_weight(visual_weight);
    scale = home_page_clamp_i32(scale, HOME_PAGE_SIDE_SCALE, HOME_PAGE_SELECTED_SCALE);
    image_x = home_page_image_x_for_weight(visual_weight);
    image_y = home_page_image_y_for_weight(visual_weight);
    opa = home_page_opa_for_weight(visual_weight);

    lv_obj_set_pos(slot->container, x, slot->base_y);
    lv_obj_set_style_opa(slot->container, opa, LV_PART_MAIN);
    if (slot->image != NULL) {
        lv_obj_set_pos(slot->image, image_x, image_y);
        lv_image_set_scale(slot->image, (uint32_t)scale);
    }
}

static size_t home_page_foreground_slot_index(const home_page_state_t *state)
{
    if (state == NULL) {
        return HOME_PAGE_CENTER_SLOT;
    }

    if (state->drag_offset < 0) {
        return HOME_PAGE_RIGHT_SLOT;
    }

    if (state->drag_offset > 0) {
        return HOME_PAGE_LEFT_SLOT;
    }

    return HOME_PAGE_CENTER_SLOT;
}

static void home_page_apply_carousel_layout(home_page_state_t *state, bool refresh_content)
{
    int center_index;
    int far_left_index;
    int left_index;
    int right_index;
    int far_right_index;
    size_t foreground_slot;

    if (state->recipe_count == 0u) {
        return;
    }

    center_index = (int)state->selected_index;
    far_left_index = home_page_wrap_index(center_index - 2, state->recipe_count);
    left_index = home_page_wrap_index(center_index - 1, state->recipe_count);
    right_index = home_page_wrap_index(center_index + 1, state->recipe_count);
    far_right_index = home_page_wrap_index(center_index + 2, state->recipe_count);

    if (refresh_content) {
        home_page_set_slot_recipe(state, 0u, (size_t)far_left_index);
        home_page_set_slot_recipe(state, 1u, (size_t)left_index);
        home_page_set_slot_recipe(state, 2u, (size_t)center_index);
        home_page_set_slot_recipe(state, 3u, (size_t)right_index);
        home_page_set_slot_recipe(state, 4u, (size_t)far_right_index);
    }

    for (size_t i = 0u; i < HOME_PAGE_CAROUSEL_SLOT_COUNT; ++i) {
        home_page_apply_slot_transform(&state->slots[i], state->drag_offset);
    }

    foreground_slot = home_page_foreground_slot_index(state);
    lv_obj_move_foreground(state->slots[foreground_slot].container);
}

static uint32_t home_page_snap_duration_for_steps(int32_t steps)
{
    if (steps <= 1) {
        return HOME_PAGE_SNAP_ANIM_MS;
    }

    return HOME_PAGE_SNAP_ANIM_MS + (uint32_t)(steps - 1) * HOME_PAGE_SNAP_EXTRA_STEP_MS;
}

static void home_page_reset_snap_state(home_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    state->dragging = false;
    state->drag_offset = 0;
    state->drag_base_offset = 0;
    state->snap_start_offset = 0;
    state->snap_target_offset = 0;
    state->snap_target_step = 0;
    state->snap_total_steps = 0;
    state->snap_completed_steps = 0;
    state->snap_step_direction = 0;
    state->snap_start_progress = 0;
    state->snap_target_progress = 0;
    state->snap_duration_ms = 0u;
    state->release_velocity = 0;
}

static void home_page_stop_snap_timer(home_page_state_t *state)
{
    if (state == NULL || state->snap_timer == NULL) {
        return;
    }

    lv_timer_del(state->snap_timer);
    state->snap_timer = NULL;
}

static void home_page_commit_snap_step(home_page_state_t *state)
{
    if (state == NULL || state->snap_step_direction == 0 || state->recipe_count == 0u) {
        return;
    }

    state->selected_index = (size_t)home_page_wrap_index((int)state->selected_index + state->snap_step_direction,
                                                         state->recipe_count);
    state->snap_completed_steps++;
    home_page_apply_carousel_layout(state, true);
}

static void home_page_finish_snap_animation(home_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    home_page_stop_snap_timer(state);

    while (state->snap_completed_steps < state->snap_total_steps) {
        home_page_commit_snap_step(state);
    }

    home_page_reset_snap_state(state);
    home_page_apply_carousel_layout(state, true);
}

static void home_page_apply_snap_progress(home_page_state_t *state, int32_t progress)
{
    int32_t abs_progress;
    int32_t completed_steps;
    int32_t step_progress;

    if (state == NULL) {
        return;
    }

    if (state->snap_total_steps == 0 && state->snap_step_direction == 0) {
        state->drag_offset = progress;
        home_page_apply_carousel_layout(state, false);
        return;
    }

    abs_progress = home_page_abs_i32(progress);
    completed_steps = abs_progress / HOME_PAGE_SWIPE_THRESHOLD;
    if (completed_steps > state->snap_total_steps) {
        completed_steps = state->snap_total_steps;
    }

    while (state->snap_completed_steps < completed_steps) {
        home_page_commit_snap_step(state);
    }

    step_progress = abs_progress - state->snap_completed_steps * HOME_PAGE_SWIPE_THRESHOLD;
    if (state->snap_step_direction > 0) {
        state->drag_offset = -step_progress;
    } else if (state->snap_step_direction < 0) {
        state->drag_offset = step_progress;
    } else {
        state->drag_offset = progress;
    }

    home_page_apply_carousel_layout(state, false);
}

static void home_page_snap_timer_cb(lv_timer_t *timer)
{
    home_page_state_t *state;
    uint32_t elapsed;
    int32_t progress;
    int32_t eased;
    int32_t snap_progress;

    state = (home_page_state_t *)lv_timer_get_user_data(timer);
    if (state == NULL) {
        return;
    }

    elapsed = lv_tick_elaps(state->snap_start_tick);
    if (elapsed >= state->snap_duration_ms) {
        home_page_apply_snap_progress(state, state->snap_target_progress);
        home_page_finish_snap_animation(state);
        return;
    }

    progress = (int32_t)(elapsed * 1024u / state->snap_duration_ms);
    eased = home_page_ease_out_quad(progress, 1024);
    snap_progress = home_page_lerp_progress_i32(state->snap_start_progress,
                                                state->snap_target_progress,
                                                eased,
                                                1024);
    home_page_apply_snap_progress(state, snap_progress);
}

static void home_page_cancel_snap_animation(home_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    home_page_stop_snap_timer(state);
    home_page_reset_snap_state(state);
}

static int32_t home_page_snap_step_for_release(const home_page_state_t *state)
{
    if (state == NULL || state->recipe_count <= 1u) {
        return 0;
    }

    if (state->release_velocity <= -HOME_PAGE_RELEASE_VELOCITY_THRESHOLD ||
        state->drag_offset <= -HOME_PAGE_DISTANCE_SNAP_THRESHOLD) {
        return 1;
    }

    if (state->release_velocity >= HOME_PAGE_RELEASE_VELOCITY_THRESHOLD ||
        state->drag_offset >= HOME_PAGE_DISTANCE_SNAP_THRESHOLD) {
        return -1;
    }

    return 0;
}

static int32_t home_page_snap_steps_for_release(const home_page_state_t *state)
{
    int32_t velocity;
    int32_t steps;

    if (state == NULL || state->recipe_count <= 1u) {
        return 0;
    }

    velocity = home_page_abs_i32(state->release_velocity);
    if (velocity >= HOME_PAGE_FLING_RELEASE_VELOCITY_THRESHOLD) {
        steps = 3;
    } else if (velocity >= HOME_PAGE_FAST_RELEASE_VELOCITY_THRESHOLD) {
        steps = 2;
    } else {
        steps = 1;
    }

    if (state->recipe_count > 0u && steps >= (int32_t)state->recipe_count) {
        steps = (int32_t)state->recipe_count - 1;
    }

    return home_page_clamp_i32(steps, 1, HOME_PAGE_MAX_INERTIA_STEPS);
}

static void home_page_start_snap_animation(home_page_state_t *state)
{
    int32_t direction;
    int32_t steps;

    if (state == NULL) {
        return;
    }

    home_page_stop_snap_timer(state);

    direction = home_page_snap_step_for_release(state);
    state->snap_step_direction = direction;
    steps = direction == 0 ? 0 : home_page_snap_steps_for_release(state);
    state->snap_total_steps = steps;
    state->snap_completed_steps = 0;
    state->snap_target_step = direction;
    state->snap_start_offset = state->drag_offset;
    state->snap_target_offset = direction > 0 ? -HOME_PAGE_SWIPE_THRESHOLD :
        (direction < 0 ? HOME_PAGE_SWIPE_THRESHOLD : 0);
    state->snap_start_progress = state->drag_offset;
    state->snap_target_progress = direction > 0 ? -steps * HOME_PAGE_SWIPE_THRESHOLD :
        (direction < 0 ? steps * HOME_PAGE_SWIPE_THRESHOLD : 0);
    state->snap_duration_ms = home_page_snap_duration_for_steps(steps);
    state->dragging = false;
    state->snap_start_tick = lv_tick_get();

    if (state->snap_start_progress == state->snap_target_progress) {
        home_page_finish_snap_animation(state);
        return;
    }

    state->snap_timer = lv_timer_create(home_page_snap_timer_cb,
                                        HOME_PAGE_SNAP_TIMER_PERIOD_MS,
                                        state);
    if (state->snap_timer == NULL) {
        home_page_apply_snap_progress(state, state->snap_target_progress);
        home_page_finish_snap_animation(state);
    }
}

static void home_page_update_drag_sample(home_page_state_t *state, int32_t x)
{
    uint32_t now;
    uint32_t elapsed;
    int32_t sample_delta;

    if (state == NULL) {
        return;
    }

    now = lv_tick_get();
    elapsed = lv_tick_elaps(state->last_drag_tick);
    sample_delta = x - state->last_drag_x;
    if (state->last_drag_tick != 0u &&
        elapsed > 0u &&
        elapsed <= 160u &&
        home_page_abs_i32(sample_delta) >= HOME_PAGE_MIN_VELOCITY_SAMPLE_DELTA) {
        state->release_velocity = (int32_t)(sample_delta * 1000 / (int32_t)elapsed);
    } else if (elapsed > 160u) {
        state->release_velocity = 0;
    }

    state->last_drag_x = x;
    state->last_drag_tick = now;
}

static void home_page_carousel_event(lv_event_t *event)
{
    home_page_state_t *state;
    lv_event_code_t code;
    lv_point_t point;

    state = (home_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL) {
        return;
    }

    code = lv_event_get_code(event);
    if (code == LV_EVENT_PRESSED) {
        lv_indev_get_point(lv_indev_active(), &point);
        home_page_cancel_snap_animation(state);
        state->drag_start_x = point.x;
        state->drag_base_offset = state->drag_offset;
        state->last_drag_x = point.x;
        state->last_drag_tick = lv_tick_get();
        state->release_velocity = 0;
        state->dragging = true;
        return;
    }

    if (code == LV_EVENT_PRESSING && state->dragging) {
        lv_indev_get_point(lv_indev_active(), &point);
        home_page_update_drag_sample(state, point.x);
        state->drag_offset = home_page_clamp_i32(state->drag_base_offset + point.x - state->drag_start_x,
                                                -HOME_PAGE_SWIPE_THRESHOLD,
                                                HOME_PAGE_SWIPE_THRESHOLD);
        home_page_apply_carousel_layout(state, false);
        return;
    }

    if (code == LV_EVENT_RELEASED && state->dragging) {
        lv_indev_get_point(lv_indev_active(), &point);
        home_page_update_drag_sample(state, point.x);
        home_page_start_snap_animation(state);
        return;
    }

    if (code == LV_EVENT_PRESS_LOST && state->dragging) {
        home_page_start_snap_animation(state);
    }
}

static void home_page_create_slot(
    home_page_state_t *state,
    size_t slot_index,
    int32_t x,
    int32_t y,
    int32_t width,
    int32_t side_image_x,
    int32_t title_x,
    int32_t drag_weight,
    bool is_center)
{
    home_page_carousel_slot_t *slot;

    slot = &state->slots[slot_index];
    slot->base_x = x;
    slot->base_y = y;
    slot->width = width;
    slot->side_image_x = side_image_x;
    slot->title_x = title_x;
    slot->drag_weight = drag_weight;
    slot->is_center = is_center;

    slot->container = lv_obj_create(state->carousel);
    if (slot->container == NULL) {
        return;
    }

    lv_obj_remove_style_all(slot->container);
    lv_obj_set_size(slot->container, width, HOME_PAGE_MENU_HEIGHT + HOME_PAGE_TITLE_HEIGHT);
    lv_obj_set_style_radius(slot->container, 0, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(slot->container, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(slot->container, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(slot->container, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_flag(slot->container, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_PRESS_LOCK);
    lv_obj_clear_flag(slot->container, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_event_cb(slot->container, home_page_carousel_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(slot->container, home_page_carousel_event, LV_EVENT_PRESSING, state);
    lv_obj_add_event_cb(slot->container, home_page_carousel_event, LV_EVENT_RELEASED, state);
    lv_obj_add_event_cb(slot->container, home_page_carousel_event, LV_EVENT_PRESS_LOST, state);

    slot->image = lv_image_create(slot->container);
    if (slot->image != NULL) {
        lv_obj_set_pos(slot->image, is_center ? HOME_PAGE_CENTER_IMAGE_X : side_image_x,
                       is_center ? HOME_PAGE_CENTER_IMAGE_Y : HOME_PAGE_SIDE_IMAGE_Y);
        lv_image_set_pivot(slot->image, 0, 0);
        lv_obj_add_flag(slot->image, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_PRESS_LOCK);
        lv_obj_add_event_cb(slot->image, home_page_carousel_event, LV_EVENT_PRESSED, state);
        lv_obj_add_event_cb(slot->image, home_page_carousel_event, LV_EVENT_PRESSING, state);
        lv_obj_add_event_cb(slot->image, home_page_carousel_event, LV_EVENT_RELEASED, state);
        lv_obj_add_event_cb(slot->image, home_page_carousel_event, LV_EVENT_PRESS_LOST, state);
    }

    slot->label = lv_label_create(slot->container);
    if (slot->label != NULL) {
        lv_obj_set_width(slot->label, HOME_PAGE_CENTER_SLOT_WIDTH);
        lv_label_set_long_mode(slot->label, LV_LABEL_LONG_DOT);
        lv_obj_set_style_text_align(slot->label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
        lv_obj_set_style_text_color(slot->label, lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_text_font(slot->label,
                                   is_center ? ui_style_font(UI_STYLE_FONT_HOME_USER) :
                                       ui_style_font(UI_STYLE_FONT_DETAILS_MENU_TITLE),
                                   LV_PART_MAIN);
        lv_obj_set_pos(slot->label, title_x, HOME_PAGE_TITLE_Y);
    }
}

static void home_page_create_carousel(home_page_state_t *state)
{
    state->carousel = lv_obj_create(state->screen);
    if (state->carousel == NULL) {
        return;
    }

    lv_obj_remove_style_all(state->carousel);
    lv_obj_set_size(state->carousel, HOME_PAGE_SCREEN_WIDTH, HOME_PAGE_SCREEN_HEIGHT - HOME_PAGE_HEADER_HEIGHT);
    lv_obj_set_pos(state->carousel, 0, HOME_PAGE_MENU_Y);
    lv_obj_set_style_bg_opa(state->carousel, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(state->carousel, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(state->carousel, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_flag(state->carousel, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_PRESS_LOCK);
    lv_obj_clear_flag(state->carousel, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_event_cb(state->carousel, home_page_carousel_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(state->carousel, home_page_carousel_event, LV_EVENT_PRESSING, state);
    lv_obj_add_event_cb(state->carousel, home_page_carousel_event, LV_EVENT_RELEASED, state);
    lv_obj_add_event_cb(state->carousel, home_page_carousel_event, LV_EVENT_PRESS_LOST, state);

    home_page_create_slot(state, HOME_PAGE_FAR_LEFT_SLOT, HOME_PAGE_FAR_LEFT_SLOT_X, HOME_PAGE_SLOT_Y,
                          HOME_PAGE_SIDE_SLOT_WIDTH, HOME_PAGE_LEFT_IMAGE_X, HOME_PAGE_LEFT_TITLE_X,
                          -2, false);
    home_page_create_slot(state, HOME_PAGE_LEFT_SLOT, HOME_PAGE_LEFT_SLOT_X, HOME_PAGE_SLOT_Y,
                          HOME_PAGE_SIDE_SLOT_WIDTH, HOME_PAGE_LEFT_IMAGE_X, HOME_PAGE_LEFT_TITLE_X,
                          -1, false);
    home_page_create_slot(state, HOME_PAGE_CENTER_SLOT, HOME_PAGE_CENTER_SLOT_X, HOME_PAGE_SLOT_Y,
                          HOME_PAGE_CENTER_SLOT_WIDTH, HOME_PAGE_CENTER_IMAGE_X, HOME_PAGE_CENTER_TITLE_X,
                          0, true);
    home_page_create_slot(state, HOME_PAGE_RIGHT_SLOT, HOME_PAGE_RIGHT_SLOT_X, HOME_PAGE_SLOT_Y,
                          HOME_PAGE_SIDE_SLOT_WIDTH, HOME_PAGE_RIGHT_IMAGE_X, HOME_PAGE_RIGHT_TITLE_X,
                          1, false);
    home_page_create_slot(state, HOME_PAGE_FAR_RIGHT_SLOT, HOME_PAGE_FAR_RIGHT_SLOT_X, HOME_PAGE_SLOT_Y,
                          HOME_PAGE_SIDE_SLOT_WIDTH, HOME_PAGE_RIGHT_IMAGE_X, HOME_PAGE_RIGHT_TITLE_X,
                          2, false);
}

void home_page_destroy(page_manager_page_ctx_t *ctx)
{
    home_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (home_page_state_t *)lv_obj_get_user_data(ctx->screen);
    if (state != NULL) {
        home_page_cancel_snap_animation(state);
    }
    free(state);
}

lv_obj_t *home_page_create(page_manager_page_ctx_t *ctx)
{
    lv_obj_t *screen;
    home_page_state_t *state;

    (void)ctx;

    state = (home_page_state_t *)calloc(1u, sizeof(*state));
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
    lv_obj_clear_flag(screen, LV_OBJ_FLAG_SCROLLABLE);

    (void)ui_style_init();
    home_page_style_screen(state);
    home_page_create_settings_button(state);
    home_page_create_carousel(state);
    home_page_create_user_switcher(state);

    if (home_page_load_recipes(state) == EP_OK) {
        home_page_apply_carousel_layout(state, true);
    }

    return screen;
}

void home_page_event(page_manager_page_ctx_t *ctx,
                     uint32_t code,
                     uint32_t wparam,
                     uint32_t lparam)
{
    home_page_state_t *state;

    (void)wparam;
    (void)lparam;

    if (ctx == NULL || ctx->screen == NULL || code != HOME_PAGE_EVENT_REFRESH) {
        return;
    }

    state = (home_page_state_t *)lv_obj_get_user_data(ctx->screen);
    if (state != NULL) {
        home_page_apply_carousel_layout(state, true);
    }
}
