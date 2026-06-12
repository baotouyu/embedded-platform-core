#include "pages/settings_page.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "lvgl.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stddef.h>
#include <stdlib.h>

#define SETTINGS_BRIGHTNESS_TITLE_TEXT "亮度"
#define SETTINGS_BRIGHTNESS_TITLE_X 372
#define SETTINGS_BRIGHTNESS_TITLE_Y 90
#define SETTINGS_BRIGHTNESS_TITLE_WIDTH 56
#define SETTINGS_BRIGHTNESS_TITLE_HEIGHT 39

#define SETTINGS_BRIGHTNESS_CONTROL_X 166
#define SETTINGS_BRIGHTNESS_CONTROL_Y 230
#define SETTINGS_BRIGHTNESS_CONTROL_WIDTH 524
#define SETTINGS_BRIGHTNESS_CONTROL_HEIGHT 100

#define SETTINGS_BRIGHTNESS_ICON_SIZE 80
#define SETTINGS_BRIGHTNESS_ICON_Y 10
#define SETTINGS_BRIGHTNESS_MIN_ICON_X 0
#define SETTINGS_BRIGHTNESS_MAX_ICON_X (SETTINGS_BRIGHTNESS_CONTROL_WIDTH - SETTINGS_BRIGHTNESS_ICON_SIZE)
#define SETTINGS_BRIGHTNESS_MIN_ICON_NAME "settings_brightness_min_icon.png"
#define SETTINGS_BRIGHTNESS_MAX_ICON_NAME "settings_brightness_max_icon.png"

#define SETTINGS_BRIGHTNESS_SEGMENT_COUNT 5u
#define SETTINGS_BRIGHTNESS_SEGMENT_X 104
#define SETTINGS_BRIGHTNESS_SEGMENT_WIDTH 44
#define SETTINGS_BRIGHTNESS_SEGMENT_HEIGHT 100
#define SETTINGS_BRIGHTNESS_SEGMENT_GAP 19
#define SETTINGS_BRIGHTNESS_SEGMENT_RADIUS 22
#define SETTINGS_BRIGHTNESS_SEGMENT_BORDER_WIDTH 3
#define SETTINGS_BRIGHTNESS_DEFAULT_INDEX 0u

typedef struct {
    lv_obj_t *screen;
    lv_obj_t *levels[SETTINGS_BRIGHTNESS_SEGMENT_COUNT];
    size_t selected_index;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char min_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char max_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
} settings_brightness_page_state_t;

static void settings_brightness_refresh(settings_brightness_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    for (size_t i = 0u; i < SETTINGS_BRIGHTNESS_SEGMENT_COUNT; ++i) {
        bool selected = i <= state->selected_index;

        if (state->levels[i] == NULL) {
            continue;
        }

        lv_obj_set_style_bg_color(state->levels[i], lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_bg_opa(state->levels[i], selected ? LV_OPA_COVER : LV_OPA_TRANSP, LV_PART_MAIN);
        lv_obj_set_style_border_color(state->levels[i], lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_border_width(state->levels[i], SETTINGS_BRIGHTNESS_SEGMENT_BORDER_WIDTH, LV_PART_MAIN);
        lv_obj_set_style_border_opa(state->levels[i], LV_OPA_COVER, LV_PART_MAIN);
    }
}

static void settings_brightness_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static void settings_brightness_min_clicked(lv_event_t *event)
{
    settings_brightness_page_state_t *state;

    state = (settings_brightness_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL || state->selected_index == 0u) {
        return;
    }

    state->selected_index--;
    settings_brightness_refresh(state);
}

static void settings_brightness_max_clicked(lv_event_t *event)
{
    settings_brightness_page_state_t *state;

    state = (settings_brightness_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL || state->selected_index + 1u >= SETTINGS_BRIGHTNESS_SEGMENT_COUNT) {
        return;
    }

    state->selected_index++;
    settings_brightness_refresh(state);
}

static void settings_brightness_level_clicked(lv_event_t *event)
{
    settings_brightness_page_state_t *state;
    lv_obj_t *target;

    state = (settings_brightness_page_state_t *)lv_event_get_user_data(event);
    target = lv_event_get_current_target_obj(event);
    if (state == NULL || target == NULL) {
        return;
    }

    for (size_t i = 0u; i < SETTINGS_BRIGHTNESS_SEGMENT_COUNT; ++i) {
        if (state->levels[i] == target) {
            state->selected_index = i;
            settings_brightness_refresh(state);
            return;
        }
    }
}

static bool settings_brightness_create_title(settings_brightness_page_state_t *state)
{
    lv_obj_t *title;

    title = lv_label_create(state->screen);
    if (title == NULL) {
        return false;
    }

    lv_obj_remove_style_all(title);
    lv_obj_set_size(title, SETTINGS_BRIGHTNESS_TITLE_WIDTH, SETTINGS_BRIGHTNESS_TITLE_HEIGHT);
    lv_obj_set_pos(title, SETTINGS_BRIGHTNESS_TITLE_X, SETTINGS_BRIGHTNESS_TITLE_Y);
    lv_obj_set_style_text_color(title, lv_color_hex(SETTINGS_PAGE_TEXT_COLOR), LV_PART_MAIN);
    lv_obj_set_style_text_font(title, ui_style_font(UI_STYLE_FONT_HOME_USER), LV_PART_MAIN);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_label_set_long_mode(title, LV_LABEL_LONG_CLIP);
    lv_label_set_text(title, SETTINGS_BRIGHTNESS_TITLE_TEXT);

    return true;
}

static bool settings_brightness_create_icon_button(lv_obj_t *parent,
                                                   const char *icon_name,
                                                   char *src,
                                                   size_t src_size,
                                                   int32_t x,
                                                   lv_event_cb_t clicked_cb,
                                                   settings_brightness_page_state_t *state)
{
    lv_obj_t *button;
    lv_obj_t *image;

    button = lv_button_create(parent);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_BRIGHTNESS_ICON_SIZE, SETTINGS_BRIGHTNESS_ICON_SIZE);
    lv_obj_set_pos(button, x, SETTINGS_BRIGHTNESS_ICON_Y);
    lv_obj_set_style_bg_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_event_cb(button, clicked_cb, LV_EVENT_CLICKED, state);

    if (ep_platform_lvgl_image_src(icon_name, src, src_size) != EP_OK) {
        return true;
    }

    image = lv_image_create(button);
    if (image == NULL) {
        return false;
    }

    lv_obj_remove_style_all(image);
    lv_obj_set_size(image, SETTINGS_BRIGHTNESS_ICON_SIZE, SETTINGS_BRIGHTNESS_ICON_SIZE);
    lv_obj_set_pos(image, 0, 0);
    lv_image_set_src(image, src);

    return true;
}

static bool settings_brightness_create_levels(lv_obj_t *parent, settings_brightness_page_state_t *state)
{
    for (size_t i = 0u; i < SETTINGS_BRIGHTNESS_SEGMENT_COUNT; ++i) {
        lv_obj_t *level;
        int32_t x;

        level = lv_button_create(parent);
        if (level == NULL) {
            return false;
        }

        x = SETTINGS_BRIGHTNESS_SEGMENT_X +
            (int32_t)i * (SETTINGS_BRIGHTNESS_SEGMENT_WIDTH + SETTINGS_BRIGHTNESS_SEGMENT_GAP);
        state->levels[i] = level;

        lv_obj_remove_style_all(level);
        lv_obj_set_size(level, SETTINGS_BRIGHTNESS_SEGMENT_WIDTH, SETTINGS_BRIGHTNESS_SEGMENT_HEIGHT);
        lv_obj_set_pos(level, x, 0);
        lv_obj_set_style_radius(level, SETTINGS_BRIGHTNESS_SEGMENT_RADIUS, LV_PART_MAIN);
        lv_obj_set_style_shadow_opa(level, LV_OPA_TRANSP, LV_PART_MAIN);
        lv_obj_add_event_cb(level, settings_brightness_level_clicked, LV_EVENT_CLICKED, state);
    }

    settings_brightness_refresh(state);
    return true;
}

static bool settings_brightness_create_control(settings_brightness_page_state_t *state)
{
    lv_obj_t *control;

    control = lv_obj_create(state->screen);
    if (control == NULL) {
        return false;
    }

    lv_obj_remove_style_all(control);
    lv_obj_set_size(control, SETTINGS_BRIGHTNESS_CONTROL_WIDTH, SETTINGS_BRIGHTNESS_CONTROL_HEIGHT);
    lv_obj_set_pos(control, SETTINGS_BRIGHTNESS_CONTROL_X, SETTINGS_BRIGHTNESS_CONTROL_Y);
    lv_obj_set_style_bg_opa(control, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(control, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(control, LV_OBJ_FLAG_SCROLLABLE);

    return settings_brightness_create_icon_button(control,
                                                  SETTINGS_BRIGHTNESS_MIN_ICON_NAME,
                                                  state->min_src,
                                                  sizeof(state->min_src),
                                                  SETTINGS_BRIGHTNESS_MIN_ICON_X,
                                                  settings_brightness_min_clicked,
                                                  state) &&
           settings_brightness_create_levels(control, state) &&
           settings_brightness_create_icon_button(control,
                                                  SETTINGS_BRIGHTNESS_MAX_ICON_NAME,
                                                  state->max_src,
                                                  sizeof(state->max_src),
                                                  SETTINGS_BRIGHTNESS_MAX_ICON_X,
                                                  settings_brightness_max_clicked,
                                                  state);
}

void settings_brightness_page_destroy(page_manager_page_ctx_t *ctx)
{
    settings_brightness_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (settings_brightness_page_state_t *)lv_obj_get_user_data(ctx->screen);
    free(state);
}

lv_obj_t *settings_brightness_page_create(page_manager_page_ctx_t *ctx)
{
    lv_obj_t *screen;
    settings_brightness_page_state_t *state;

    (void)ctx;

    state = (settings_brightness_page_state_t *)calloc(1u, sizeof(*state));
    if (state == NULL) {
        return NULL;
    }

    screen = lv_obj_create(NULL);
    if (screen == NULL) {
        free(state);
        return NULL;
    }

    state->screen = screen;
    state->selected_index = SETTINGS_BRIGHTNESS_DEFAULT_INDEX;
    lv_obj_set_user_data(screen, state);

    (void)ui_style_init();
    settings_common_style_screen(screen);

    if (!settings_common_create_icon_button(screen,
                                            SETTINGS_PAGE_BACK_ICON_NAME,
                                            state->back_src,
                                            sizeof(state->back_src),
                                            SETTINGS_PAGE_BACK_X,
                                            SETTINGS_PAGE_BACK_Y,
                                            SETTINGS_PAGE_BACK_SIZE,
                                            settings_brightness_back_clicked) ||
        !settings_brightness_create_title(state) ||
        !settings_brightness_create_control(state)) {
        lv_obj_delete(screen);
        free(state);
        return NULL;
    }

    return screen;
}

void settings_brightness_page_event(page_manager_page_ctx_t *ctx,
                                    uint32_t code,
                                    uint32_t wparam,
                                    uint32_t lparam)
{
    (void)ctx;
    (void)code;
    (void)wparam;
    (void)lparam;
}
