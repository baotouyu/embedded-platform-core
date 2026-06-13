#include "pages/running_page.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "ep_simple_recipe.h"
#include "lvgl.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define RUNNING_PAGE_SRC_BUFFER_SIZE 160
#define RUNNING_PAGE_RECIPE_DB_NAME "recipelib.db"
#define RUNNING_PAGE_BG_IMAGE_NAME "running_bg.png"
#define RUNNING_PAGE_START_ICON_NAME "running_start.png"
#define RUNNING_PAGE_PARAM_ICON_TEMPERATURE_NAME "running_param_temperature.png"
#define RUNNING_PAGE_PARAM_ICON_PRE_SOAK_NAME "running_param_pre_soak.png"
#define RUNNING_PAGE_PARAM_ICON_COFFEE_VOLUME_NAME "running_param_coffee_volume.png"
#define RUNNING_PAGE_PARAM_ICON_HOT_WATER_NAME "running_param_hot_water.png"
#define RUNNING_PAGE_PARAM_ICON_MILK_NAME "running_param_milk.png"
#define RUNNING_PAGE_STRENGTH_MINUS_ICON_NAME "running_minus.png"
#define RUNNING_PAGE_STRENGTH_PLUS_ICON_NAME "running_plus.png"
#define RUNNING_PAGE_STRENGTH_RING_BASE_IMAGE_NAME "running_ring_base.png"
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_IMAGE_NAME "running_ring_light.png"
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_IMAGE_NAME "running_ring_medium.png"
#define RUNNING_PAGE_STRENGTH_RING_STRONG_IMAGE_NAME "running_ring_strong.png"
#define RUNNING_PAGE_RECIPE_IMAGE_FALLBACK_X 47
#define RUNNING_PAGE_RECIPE_IMAGE_FALLBACK_Y 139
#define RUNNING_PAGE_RECIPE_IMAGE_SIZE 180
#define RUNNING_PAGE_RECIPE_ALPHA_THRESHOLD 8u
#define RUNNING_PAGE_RECIPE_ANCHOR_BAND_MIN_HEIGHT 8u
#define RUNNING_PAGE_IMAGE_SCALE_BASE 256u
#define RUNNING_PAGE_RECIPE_TARGET_CENTER_X (RUNNING_PAGE_STRENGTH_RING_X + RUNNING_PAGE_STRENGTH_RING_WIDTH / 2)
#define RUNNING_PAGE_RECIPE_TARGET_CENTER_OFFSET_X (-5)
#define RUNNING_PAGE_RECIPE_TARGET_BOTTOM_OFFSET_Y 50
#define RUNNING_PAGE_RECIPE_TARGET_BOTTOM_Y (RUNNING_PAGE_STRENGTH_RING_Y + RUNNING_PAGE_RECIPE_TARGET_BOTTOM_OFFSET_Y)
#define RUNNING_PAGE_TITLE_X RUNNING_PAGE_STRENGTH_CONTROL_X
#define RUNNING_PAGE_TITLE_Y 72
#define RUNNING_PAGE_TITLE_WIDTH RUNNING_PAGE_STRENGTH_CONTROL_WIDTH
#define RUNNING_PAGE_TITLE_HEIGHT 40
#define RUNNING_PAGE_STRENGTH_CONTROL_X 32
#define RUNNING_PAGE_STRENGTH_CONTROL_Y 112
#define RUNNING_PAGE_STRENGTH_CONTROL_WIDTH 224
#define RUNNING_PAGE_STRENGTH_CONTROL_HEIGHT 44
#define RUNNING_PAGE_STRENGTH_BUTTON_SIZE 44
#define RUNNING_PAGE_STRENGTH_MINUS_X 0
#define RUNNING_PAGE_STRENGTH_PLUS_X (RUNNING_PAGE_STRENGTH_CONTROL_WIDTH - RUNNING_PAGE_STRENGTH_BUTTON_SIZE)
#define RUNNING_PAGE_STRENGTH_TEXT_WIDTH (RUNNING_PAGE_STRENGTH_CONTROL_WIDTH - RUNNING_PAGE_STRENGTH_BUTTON_SIZE * 2)
#define RUNNING_PAGE_STRENGTH_RING_X 63
#define RUNNING_PAGE_STRENGTH_RING_Y 271
#define RUNNING_PAGE_STRENGTH_RING_WIDTH 160
#define RUNNING_PAGE_STRENGTH_RING_HEIGHT 80
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_X (RUNNING_PAGE_STRENGTH_RING_X + 84)
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_Y RUNNING_PAGE_STRENGTH_RING_Y
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_WIDTH 76
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_HEIGHT 66
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_X (RUNNING_PAGE_STRENGTH_RING_X + 26)
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_Y RUNNING_PAGE_STRENGTH_RING_Y
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_WIDTH 134
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_HEIGHT 80
#define RUNNING_PAGE_STRENGTH_RING_STRONG_X RUNNING_PAGE_STRENGTH_RING_X
#define RUNNING_PAGE_STRENGTH_RING_STRONG_Y RUNNING_PAGE_STRENGTH_RING_Y
#define RUNNING_PAGE_STRENGTH_RING_STRONG_WIDTH 160
#define RUNNING_PAGE_STRENGTH_RING_STRONG_HEIGHT 80
#define RUNNING_PAGE_START_X 114
#define RUNNING_PAGE_START_Y (SETTINGS_PAGE_SCREEN_HEIGHT - 44 - RUNNING_PAGE_START_SIZE)
#define RUNNING_PAGE_START_SIZE 60
#define RUNNING_PAGE_PARAM_KEY_TEMPERATURE "temperature"
#define RUNNING_PAGE_PARAM_KEY_PRE_SOAK "pre_soak"
#define RUNNING_PAGE_PARAM_KEY_DISCHARGE "discharge"
#define RUNNING_PAGE_PARAM_KEY_HOT_WATER "hot_water"
#define RUNNING_PAGE_PARAM_KEY_MILK_FOAM "milk_foam_volume"
#define RUNNING_PAGE_PARAM_KEY_MILK_QUANTITY "milk_quantity"
#define RUNNING_PAGE_PARAM_KEY_COFFEE_POWDER "coffee_powder_quantity"
#define RUNNING_PAGE_PARAM_KEY_COFFEE_TYPE "coffee_type"
#define RUNNING_PAGE_PARAM_MAX_ROWS 5u
#define RUNNING_PAGE_PARAM_ICON_COUNT 5u
#define RUNNING_PAGE_PARAM_AREA_X 356
#define RUNNING_PAGE_PARAM_AREA_Y 70
#define RUNNING_PAGE_PARAM_ROW_GAP 82
#define RUNNING_PAGE_PARAM_GROUP_WIDTH 444
#define RUNNING_PAGE_PARAM_GROUP_HEIGHT 74
#define RUNNING_PAGE_PARAM_SINGLE_AREA_Y ((SETTINGS_PAGE_SCREEN_HEIGHT - RUNNING_PAGE_PARAM_GROUP_HEIGHT) / 2)
#define RUNNING_PAGE_PARAM_TITLE_X 0
#define RUNNING_PAGE_PARAM_TITLE_Y 0
#define RUNNING_PAGE_PARAM_TITLE_WIDTH 132
#define RUNNING_PAGE_PARAM_TITLE_HEIGHT 32
#define RUNNING_PAGE_PARAM_ICON_X 0
#define RUNNING_PAGE_PARAM_ICON_Y 36
#define RUNNING_PAGE_PARAM_ICON_SIZE 32
#define RUNNING_PAGE_PARAM_VALUE_X 174
#define RUNNING_PAGE_PARAM_VALUE_Y RUNNING_PAGE_PARAM_TITLE_Y
#define RUNNING_PAGE_PARAM_VALUE_WIDTH 130
#define RUNNING_PAGE_PARAM_VALUE_HEIGHT 32
#define RUNNING_PAGE_PARAM_TRACK_X 64
#define RUNNING_PAGE_PARAM_TRACK_Y 48
#define RUNNING_PAGE_PARAM_TRACK_WIDTH 270
#define RUNNING_PAGE_PARAM_TRACK_HEIGHT 10
#define RUNNING_PAGE_PARAM_TRACK_RADIUS 5
#define RUNNING_PAGE_PARAM_KNOB_SIZE 36
#define RUNNING_PAGE_PARAM_KNOB_Y (RUNNING_PAGE_PARAM_TRACK_Y - ((RUNNING_PAGE_PARAM_KNOB_SIZE - RUNNING_PAGE_PARAM_TRACK_HEIGHT) / 2))
#define RUNNING_PAGE_PARAM_MAX_LABEL_X 366
#define RUNNING_PAGE_PARAM_MAX_LABEL_Y 34
#define RUNNING_PAGE_PARAM_MAX_LABEL_WIDTH 78
#define RUNNING_PAGE_PARAM_MAX_LABEL_HEIGHT 32
#define RUNNING_PAGE_PARAM_TRACK_COLOR 0x4D4D4D
#define RUNNING_PAGE_PARAM_FILL_COLOR 0xC99868

typedef enum {
    RUNNING_PAGE_STRENGTH_LIGHT = 0,
    RUNNING_PAGE_STRENGTH_MEDIUM,
    RUNNING_PAGE_STRENGTH_STRONG,
} running_page_strength_t;

#define RUNNING_PAGE_STRENGTH_DEFAULT RUNNING_PAGE_STRENGTH_MEDIUM

typedef struct {
    uint32_t x1;
    uint32_t y1;
    uint32_t x2;
    uint32_t y2;
    uint32_t bottom_anchor_x;
    bool valid;
} running_page_recipe_bounds_t;

typedef struct {
    uint32_t scale;
    int32_t x;
    int32_t y;
} running_page_recipe_layout_t;

typedef struct {
    char recipe_id[EP_SIMPLE_RECIPE_ID_MAX_LEN];
    char recipe_name[EP_SIMPLE_RECIPE_NAME_MAX_LEN];
    char image_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
} running_page_recipe_context_t;

typedef struct {
    const char *key;
    const char *title;
    const char *unit;
    const char *icon_name;
} running_page_param_spec_t;

typedef struct {
    const running_page_param_spec_t *spec;
    int32_t min;
    int32_t max;
    int32_t value;
    char icon_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    lv_obj_t *group;
    lv_obj_t *fill;
    lv_obj_t *knob;
    lv_obj_t *value_label;
} running_page_param_row_t;

typedef struct {
    lv_obj_t *screen;
    lv_obj_t *strength_control;
    lv_obj_t *strength_label;
    lv_obj_t *strength_overlay;
    ep_simple_recipe_detail_t recipe_detail;
    running_page_param_row_t param_rows[RUNNING_PAGE_PARAM_MAX_ROWS];
    size_t param_row_count;
    char bg_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char start_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char strength_minus_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_plus_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_ring_base_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_ring_light_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_ring_medium_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_ring_strong_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char recipe_image_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char recipe_id[EP_SIMPLE_RECIPE_ID_MAX_LEN];
    char recipe_name[EP_SIMPLE_RECIPE_NAME_MAX_LEN];
    running_page_strength_t strength;
} running_page_state_t;

static running_page_recipe_context_t running_page_pending_recipe;

static const running_page_param_spec_t running_page_param_specs[] = {
    {RUNNING_PAGE_PARAM_KEY_TEMPERATURE, "萃取温度", "℃", RUNNING_PAGE_PARAM_ICON_TEMPERATURE_NAME},
    {RUNNING_PAGE_PARAM_KEY_PRE_SOAK, "预浸泡", "s", RUNNING_PAGE_PARAM_ICON_PRE_SOAK_NAME},
    {RUNNING_PAGE_PARAM_KEY_DISCHARGE, "咖啡容量", "ml", RUNNING_PAGE_PARAM_ICON_COFFEE_VOLUME_NAME},
    {RUNNING_PAGE_PARAM_KEY_HOT_WATER, "热水容量", "ml", RUNNING_PAGE_PARAM_ICON_HOT_WATER_NAME},
    {RUNNING_PAGE_PARAM_KEY_MILK_FOAM, "制作时间", "s", RUNNING_PAGE_PARAM_ICON_MILK_NAME},
    {RUNNING_PAGE_PARAM_KEY_MILK_QUANTITY, "牛奶容量", "ml", RUNNING_PAGE_PARAM_ICON_MILK_NAME},
};

static void running_page_copy_string(char *dst, size_t dst_size, const char *src)
{
    if (dst == NULL || dst_size == 0u) {
        return;
    }

    if (src == NULL) {
        dst[0] = '\0';
        return;
    }

    (void)snprintf(dst, dst_size, "%s", src);
}

void running_page_set_recipe_context(const ep_simple_recipe_item_t *recipe, const char *image_src)
{
    running_page_copy_string(running_page_pending_recipe.image_src,
                             sizeof(running_page_pending_recipe.image_src),
                             image_src);

    if (recipe == NULL) {
        running_page_pending_recipe.recipe_id[0] = '\0';
        running_page_pending_recipe.recipe_name[0] = '\0';
        return;
    }

    running_page_copy_string(running_page_pending_recipe.recipe_id,
                             sizeof(running_page_pending_recipe.recipe_id),
                             recipe->id);
    running_page_copy_string(running_page_pending_recipe.recipe_name,
                             sizeof(running_page_pending_recipe.recipe_name),
                             recipe->name);
}

static void running_page_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static const char *running_page_strength_text(running_page_strength_t strength)
{
    if (strength == RUNNING_PAGE_STRENGTH_LIGHT) {
        return "清淡";
    }

    if (strength == RUNNING_PAGE_STRENGTH_STRONG) {
        return "浓郁";
    }

    return "适中";
}

static void running_page_refresh_strength(running_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    if (state->strength_label != NULL) {
        lv_label_set_text(state->strength_label, running_page_strength_text(state->strength));
    }

    if (state->strength_overlay == NULL) {
        return;
    }

    lv_obj_clear_flag(state->strength_overlay, LV_OBJ_FLAG_HIDDEN);
    if (state->strength == RUNNING_PAGE_STRENGTH_LIGHT) {
        lv_obj_set_pos(state->strength_overlay, RUNNING_PAGE_STRENGTH_RING_LIGHT_X, RUNNING_PAGE_STRENGTH_RING_LIGHT_Y);
        lv_obj_set_size(state->strength_overlay,
                        RUNNING_PAGE_STRENGTH_RING_LIGHT_WIDTH,
                        RUNNING_PAGE_STRENGTH_RING_LIGHT_HEIGHT);
        lv_image_set_src(state->strength_overlay, state->strength_ring_light_src);
    } else if (state->strength == RUNNING_PAGE_STRENGTH_MEDIUM) {
        lv_obj_set_pos(state->strength_overlay, RUNNING_PAGE_STRENGTH_RING_MEDIUM_X, RUNNING_PAGE_STRENGTH_RING_MEDIUM_Y);
        lv_obj_set_size(state->strength_overlay,
                        RUNNING_PAGE_STRENGTH_RING_MEDIUM_WIDTH,
                        RUNNING_PAGE_STRENGTH_RING_MEDIUM_HEIGHT);
        lv_image_set_src(state->strength_overlay, state->strength_ring_medium_src);
    } else {
        lv_obj_set_pos(state->strength_overlay, RUNNING_PAGE_STRENGTH_RING_STRONG_X, RUNNING_PAGE_STRENGTH_RING_STRONG_Y);
        lv_obj_set_size(state->strength_overlay,
                        RUNNING_PAGE_STRENGTH_RING_STRONG_WIDTH,
                        RUNNING_PAGE_STRENGTH_RING_STRONG_HEIGHT);
        lv_image_set_src(state->strength_overlay, state->strength_ring_strong_src);
    }
}

static void running_page_strength_minus_clicked(lv_event_t *event)
{
    running_page_state_t *state;

    state = (running_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL || state->strength == RUNNING_PAGE_STRENGTH_LIGHT) {
        return;
    }

    state->strength = (running_page_strength_t)(state->strength - 1);
    running_page_refresh_strength(state);
}

static void running_page_strength_plus_clicked(lv_event_t *event)
{
    running_page_state_t *state;

    state = (running_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL || state->strength == RUNNING_PAGE_STRENGTH_STRONG) {
        return;
    }

    state->strength = (running_page_strength_t)(state->strength + 1);
    running_page_refresh_strength(state);
}

static void running_page_start_clicked(lv_event_t *event)
{
    (void)event;
}

static void running_page_create_background(running_page_state_t *state)
{
    lv_obj_t *bg;

    if (state == NULL || state->screen == NULL) {
        return;
    }

    if (ep_platform_lvgl_image_src(RUNNING_PAGE_BG_IMAGE_NAME,
                                   state->bg_src,
                                   sizeof(state->bg_src)) != EP_OK) {
        return;
    }

    bg = lv_image_create(state->screen);
    if (bg == NULL) {
        return;
    }

    lv_image_set_src(bg, state->bg_src);
    lv_obj_set_size(bg, SETTINGS_PAGE_SCREEN_WIDTH, SETTINGS_PAGE_SCREEN_HEIGHT);
    lv_obj_set_pos(bg, 0, 0);
    lv_obj_move_background(bg);
}

static void running_page_create_recipe_title(running_page_state_t *state)
{
    lv_obj_t *title;

    if (state == NULL || state->screen == NULL || state->recipe_name[0] == '\0') {
        return;
    }

    title = lv_label_create(state->screen);
    if (title == NULL) {
        return;
    }

    lv_obj_remove_style_all(title);
    lv_obj_set_pos(title, RUNNING_PAGE_TITLE_X, RUNNING_PAGE_TITLE_Y);
    lv_obj_set_size(title, RUNNING_PAGE_TITLE_WIDTH, RUNNING_PAGE_TITLE_HEIGHT);
    lv_obj_set_style_text_color(title, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(title, ui_style_font(UI_STYLE_FONT_HOME_USER), LV_PART_MAIN);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_label_set_long_mode(title, LV_LABEL_LONG_CLIP);
    lv_label_set_text(title, state->recipe_name);
}

static bool running_page_create_image(lv_obj_t *parent,
                                      const char *src,
                                      int32_t x,
                                      int32_t y,
                                      int32_t width,
                                      int32_t height,
                                      lv_obj_t **out_image)
{
    lv_obj_t *image;

    if (parent == NULL || src == NULL || src[0] == '\0') {
        return false;
    }

    image = lv_image_create(parent);
    if (image == NULL) {
        return false;
    }

    lv_image_set_src(image, src);
    lv_obj_set_size(image, width, height);
    lv_obj_set_pos(image, x, y);

    if (out_image != NULL) {
        *out_image = image;
    }

    return true;
}

static bool running_page_create_strength_button(lv_obj_t *parent,
                                                running_page_state_t *state,
                                                const char *icon_name,
                                                char *src,
                                                size_t src_size,
                                                int32_t x,
                                                lv_event_cb_t clicked_cb)
{
    lv_obj_t *button;
    lv_obj_t *icon;

    if (parent == NULL || state == NULL) {
        return false;
    }

    button = lv_button_create(parent);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, RUNNING_PAGE_STRENGTH_BUTTON_SIZE, RUNNING_PAGE_STRENGTH_BUTTON_SIZE);
    lv_obj_set_pos(button, x, 0);
    lv_obj_set_style_bg_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_event_cb(button, clicked_cb, LV_EVENT_CLICKED, state);

    if (ep_platform_lvgl_image_src(icon_name, src, src_size) != EP_OK) {
        return true;
    }

    icon = lv_image_create(button);
    if (icon == NULL) {
        return false;
    }

    lv_obj_remove_style_all(icon);
    lv_obj_set_size(icon, RUNNING_PAGE_STRENGTH_BUTTON_SIZE, RUNNING_PAGE_STRENGTH_BUTTON_SIZE);
    lv_image_set_src(icon, src);
    lv_obj_align(icon, LV_ALIGN_CENTER, 0, 0);

    return true;
}

static void running_page_create_strength_ring(running_page_state_t *state)
{
    if (state == NULL || state->screen == NULL) {
        return;
    }

    if (ep_platform_lvgl_image_src(RUNNING_PAGE_STRENGTH_RING_BASE_IMAGE_NAME,
                                   state->strength_ring_base_src,
                                   sizeof(state->strength_ring_base_src)) == EP_OK) {
        (void)running_page_create_image(state->screen,
                                        state->strength_ring_base_src,
                                        RUNNING_PAGE_STRENGTH_RING_X,
                                        RUNNING_PAGE_STRENGTH_RING_Y,
                                        RUNNING_PAGE_STRENGTH_RING_WIDTH,
                                        RUNNING_PAGE_STRENGTH_RING_HEIGHT,
                                        NULL);
    }

    (void)ep_platform_lvgl_image_src(RUNNING_PAGE_STRENGTH_RING_LIGHT_IMAGE_NAME,
                                     state->strength_ring_light_src,
                                     sizeof(state->strength_ring_light_src));
    (void)ep_platform_lvgl_image_src(RUNNING_PAGE_STRENGTH_RING_MEDIUM_IMAGE_NAME,
                                     state->strength_ring_medium_src,
                                     sizeof(state->strength_ring_medium_src));
    (void)ep_platform_lvgl_image_src(RUNNING_PAGE_STRENGTH_RING_STRONG_IMAGE_NAME,
                                     state->strength_ring_strong_src,
                                     sizeof(state->strength_ring_strong_src));

    (void)running_page_create_image(state->screen,
                                    state->strength_ring_medium_src,
                                    RUNNING_PAGE_STRENGTH_RING_MEDIUM_X,
                                    RUNNING_PAGE_STRENGTH_RING_MEDIUM_Y,
                                    RUNNING_PAGE_STRENGTH_RING_MEDIUM_WIDTH,
                                    RUNNING_PAGE_STRENGTH_RING_MEDIUM_HEIGHT,
                                    &state->strength_overlay);
    running_page_refresh_strength(state);
}

static void running_page_create_start_button(running_page_state_t *state)
{
    lv_obj_t *button;
    lv_obj_t *icon;

    if (state == NULL || state->screen == NULL) {
        return;
    }

    button = lv_button_create(state->screen);
    if (button == NULL) {
        return;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, RUNNING_PAGE_START_SIZE, RUNNING_PAGE_START_SIZE);
    lv_obj_set_pos(button, RUNNING_PAGE_START_X, RUNNING_PAGE_START_Y);
    lv_obj_set_style_bg_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_event_cb(button, running_page_start_clicked, LV_EVENT_CLICKED, state);

    if (ep_platform_lvgl_image_src(RUNNING_PAGE_START_ICON_NAME,
                                   state->start_src,
                                   sizeof(state->start_src)) != EP_OK) {
        return;
    }

    icon = lv_image_create(button);
    if (icon == NULL) {
        return;
    }

    lv_obj_remove_style_all(icon);
    lv_obj_set_size(icon, RUNNING_PAGE_START_SIZE, RUNNING_PAGE_START_SIZE);
    lv_image_set_src(icon, state->start_src);
    lv_obj_align(icon, LV_ALIGN_CENTER, 0, 0);
}

static void running_page_create_strength_controls(running_page_state_t *state)
{
    if (state == NULL || state->screen == NULL) {
        return;
    }

    state->strength_control = lv_obj_create(state->screen);
    if (state->strength_control == NULL) {
        return;
    }

    lv_obj_remove_style_all(state->strength_control);
    lv_obj_set_size(state->strength_control,
                    RUNNING_PAGE_STRENGTH_CONTROL_WIDTH,
                    RUNNING_PAGE_STRENGTH_CONTROL_HEIGHT);
    lv_obj_set_pos(state->strength_control, RUNNING_PAGE_STRENGTH_CONTROL_X, RUNNING_PAGE_STRENGTH_CONTROL_Y);
    lv_obj_clear_flag(state->strength_control, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_opa(state->strength_control, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(state->strength_control, LV_OPA_TRANSP, LV_PART_MAIN);

    (void)running_page_create_strength_button(state->strength_control,
                                              state,
                                              RUNNING_PAGE_STRENGTH_MINUS_ICON_NAME,
                                              state->strength_minus_src,
                                              sizeof(state->strength_minus_src),
                                              RUNNING_PAGE_STRENGTH_MINUS_X,
                                              running_page_strength_minus_clicked);
    (void)running_page_create_strength_button(state->strength_control,
                                              state,
                                              RUNNING_PAGE_STRENGTH_PLUS_ICON_NAME,
                                              state->strength_plus_src,
                                              sizeof(state->strength_plus_src),
                                              RUNNING_PAGE_STRENGTH_PLUS_X,
                                              running_page_strength_plus_clicked);

    state->strength_label = lv_label_create(state->strength_control);
    if (state->strength_label != NULL) {
        lv_obj_remove_style_all(state->strength_label);
        lv_obj_set_width(state->strength_label, RUNNING_PAGE_STRENGTH_TEXT_WIDTH);
        lv_obj_set_height(state->strength_label, LV_SIZE_CONTENT);
        lv_obj_set_style_text_color(state->strength_label, lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_text_font(state->strength_label, ui_style_font(UI_STYLE_FONT_HOME_USER), LV_PART_MAIN);
        lv_obj_set_style_text_align(state->strength_label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
        lv_label_set_long_mode(state->strength_label, LV_LABEL_LONG_CLIP);
        lv_obj_align(state->strength_label, LV_ALIGN_CENTER, 0, 0);
    }

    running_page_refresh_strength(state);
}

static bool running_page_parse_i32(const char *text, int32_t *out_value)
{
    char *end;
    long value;

    if (text == NULL || text[0] == '\0' || out_value == NULL) {
        return false;
    }

    value = strtol(text, &end, 10);
    if (end == text || *end != '\0') {
        return false;
    }

    *out_value = (int32_t)value;
    return true;
}

static int32_t running_page_clamp_i32(int32_t value, int32_t min, int32_t max)
{
    if (value < min) {
        return min;
    }
    if (value > max) {
        return max;
    }
    return value;
}

static const ep_simple_recipe_param_t *running_page_find_param(const ep_simple_recipe_step_t *step, const char *key)
{
    size_t i;

    if (step == NULL || key == NULL) {
        return NULL;
    }

    for (i = 0u; i < step->param_count; ++i) {
        if (strcmp(step->params[i].key, key) == 0) {
            return &step->params[i];
        }
    }

    return NULL;
}

static bool running_page_param_values_from_recipe(const ep_simple_recipe_param_t *param,
                                                  int32_t *out_min,
                                                  int32_t *out_max,
                                                  int32_t *out_value)
{
    int32_t min;
    int32_t max;
    int32_t value;

    if (param == NULL || out_min == NULL || out_max == NULL || out_value == NULL) {
        return false;
    }

    if (!running_page_parse_i32(param->ctl_val, &value)) {
        return false;
    }

    if (!running_page_parse_i32(param->min_val, &min) || !running_page_parse_i32(param->max_val, &max)) {
        return false;
    }
    if (min > max) {
        int32_t tmp = min;
        min = max;
        max = tmp;
    }
    if (min == max) {
        return false;
    }

    *out_min = min;
    *out_max = max;
    *out_value = running_page_clamp_i32(value, min, max);
    return true;
}

static bool running_page_param_is_adjustable(const ep_simple_recipe_param_t *param)
{
    int32_t min;
    int32_t max;
    int32_t value;

    return running_page_param_values_from_recipe(param, &min, &max, &value);
}

static bool running_page_has_adjustable_strength(const running_page_state_t *state)
{
    const ep_simple_recipe_step_t *step;

    if (state == NULL || state->recipe_detail.step_count == 0u) {
        return false;
    }

    step = &state->recipe_detail.steps[0];
    return running_page_param_is_adjustable(running_page_find_param(step, RUNNING_PAGE_PARAM_KEY_COFFEE_POWDER));
}

static int32_t running_page_param_progress_width_for_value(const running_page_param_row_t *row, int32_t value)
{
    int32_t range;

    if (row == NULL || row->max <= row->min) {
        return 0;
    }

    value = running_page_clamp_i32(value, row->min, row->max);
    range = row->max - row->min;
    return (RUNNING_PAGE_PARAM_TRACK_WIDTH * (value - row->min)) / range;
}

static int32_t running_page_param_knob_x_for_value(const running_page_param_row_t *row, int32_t value)
{
    return RUNNING_PAGE_PARAM_TRACK_X + running_page_param_progress_width_for_value(row, value) -
           (RUNNING_PAGE_PARAM_KNOB_SIZE / 2);
}

static int32_t running_page_param_value_for_point(const running_page_param_row_t *row, const lv_point_t *point)
{
    lv_area_t group_coords;
    int32_t relative_x;
    int32_t range;

    if (row == NULL || row->group == NULL || point == NULL || row->max <= row->min) {
        return 0;
    }

    lv_obj_get_coords(row->group, &group_coords);
    relative_x = point->x - group_coords.x1 - RUNNING_PAGE_PARAM_TRACK_X;
    if (relative_x <= 0) {
        return row->min;
    }
    if (relative_x >= RUNNING_PAGE_PARAM_TRACK_WIDTH) {
        return row->max;
    }

    range = row->max - row->min;
    return row->min + ((relative_x * range) + (RUNNING_PAGE_PARAM_TRACK_WIDTH / 2)) /
                          RUNNING_PAGE_PARAM_TRACK_WIDTH;
}

static void running_page_set_param_value(running_page_param_row_t *row, int32_t value)
{
    int32_t progress_width;

    if (row == NULL) {
        return;
    }

    row->value = running_page_clamp_i32(value, row->min, row->max);
    progress_width = running_page_param_progress_width_for_value(row, row->value);

    if (row->fill != NULL) {
        lv_obj_set_width(row->fill, progress_width);
    }
    if (row->knob != NULL) {
        lv_obj_set_x(row->knob, running_page_param_knob_x_for_value(row, row->value));
    }
    if (row->value_label != NULL && row->spec != NULL) {
        lv_label_set_text_fmt(row->value_label, "%d%s", row->value, row->spec->unit);
    }
}

static void running_page_param_event(lv_event_t *event)
{
    running_page_param_row_t *row;
    lv_point_t point;

    row = (running_page_param_row_t *)lv_event_get_user_data(event);
    if (row == NULL) {
        return;
    }

    lv_indev_get_point(lv_indev_active(), &point);
    running_page_set_param_value(row, running_page_param_value_for_point(row, &point));
}

static lv_obj_t *running_page_create_progress_segment(lv_obj_t *parent,
                                                      int32_t x,
                                                      int32_t y,
                                                      int32_t width,
                                                      int32_t height,
                                                      uint32_t color,
                                                      int32_t radius)
{
    lv_obj_t *segment;

    segment = lv_obj_create(parent);
    if (segment == NULL) {
        return NULL;
    }

    lv_obj_remove_style_all(segment);
    lv_obj_set_size(segment, width, height);
    lv_obj_set_pos(segment, x, y);
    lv_obj_set_style_bg_color(segment, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(segment, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(segment, radius, LV_PART_MAIN);
    lv_obj_set_style_border_opa(segment, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(segment, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(segment, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(segment, LV_OBJ_FLAG_CLICKABLE);

    return segment;
}

static int32_t running_page_param_row_y_for_count(size_t row_index, size_t total_row_count)
{
    return total_row_count == 1u ? RUNNING_PAGE_PARAM_SINGLE_AREA_Y :
                                  RUNNING_PAGE_PARAM_AREA_Y + (int32_t)row_index * RUNNING_PAGE_PARAM_ROW_GAP;
}

static bool running_page_create_param_row(lv_obj_t *parent,
                                          running_page_param_row_t *row,
                                          const running_page_param_spec_t *spec,
                                          const ep_simple_recipe_param_t *param,
                                          size_t row_index,
                                          size_t total_row_count)
{
    lv_obj_t *group;
    lv_obj_t *title;
    lv_obj_t *icon;
    lv_obj_t *track;
    lv_obj_t *max_label;
    int32_t min;
    int32_t max;
    int32_t value;

    if (parent == NULL || row == NULL || spec == NULL ||
        !running_page_param_values_from_recipe(param, &min, &max, &value)) {
        return false;
    }

    *row = (running_page_param_row_t){0};
    row->spec = spec;
    row->min = min;
    row->max = max;
    row->value = value;

    group = lv_obj_create(parent);
    if (group == NULL) {
        return false;
    }
    row->group = group;
    lv_obj_remove_style_all(group);
    lv_obj_set_size(group, RUNNING_PAGE_PARAM_GROUP_WIDTH, RUNNING_PAGE_PARAM_GROUP_HEIGHT);
    lv_obj_set_pos(group,
                   RUNNING_PAGE_PARAM_AREA_X,
                   running_page_param_row_y_for_count(row_index, total_row_count));
    lv_obj_set_style_bg_opa(group, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(group, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(group, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(group, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(group, running_page_param_event, LV_EVENT_PRESSED, row);
    lv_obj_add_event_cb(group, running_page_param_event, LV_EVENT_PRESSING, row);

    title = lv_label_create(group);
    if (title != NULL) {
        lv_obj_remove_style_all(title);
        lv_obj_set_pos(title, RUNNING_PAGE_PARAM_TITLE_X, RUNNING_PAGE_PARAM_TITLE_Y);
        lv_obj_set_size(title, RUNNING_PAGE_PARAM_TITLE_WIDTH, RUNNING_PAGE_PARAM_TITLE_HEIGHT);
        lv_obj_set_style_text_color(title, lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_text_font(title, ui_style_font(UI_STYLE_FONT_DETAILS_MENU_VALUE), LV_PART_MAIN);
        lv_label_set_long_mode(title, LV_LABEL_LONG_CLIP);
        lv_label_set_text(title, spec->title);
    }

    if (ep_platform_lvgl_image_src(spec->icon_name, row->icon_src, sizeof(row->icon_src)) == EP_OK) {
        icon = lv_image_create(group);
        if (icon != NULL) {
            lv_obj_remove_style_all(icon);
            lv_obj_set_size(icon, RUNNING_PAGE_PARAM_ICON_SIZE, RUNNING_PAGE_PARAM_ICON_SIZE);
            lv_obj_set_pos(icon, RUNNING_PAGE_PARAM_ICON_X, RUNNING_PAGE_PARAM_ICON_Y);
            lv_image_set_src(icon, row->icon_src);
        }
    }

    row->value_label = lv_label_create(group);
    if (row->value_label != NULL) {
        lv_obj_remove_style_all(row->value_label);
        lv_obj_set_pos(row->value_label, RUNNING_PAGE_PARAM_VALUE_X, RUNNING_PAGE_PARAM_VALUE_Y);
        lv_obj_set_size(row->value_label, RUNNING_PAGE_PARAM_VALUE_WIDTH, RUNNING_PAGE_PARAM_VALUE_HEIGHT);
        lv_obj_set_style_text_color(row->value_label, lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_text_font(row->value_label, ui_style_font(UI_STYLE_FONT_HOME_SIDE), LV_PART_MAIN);
        lv_obj_set_style_text_align(row->value_label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    }

    track = running_page_create_progress_segment(group,
                                                 RUNNING_PAGE_PARAM_TRACK_X,
                                                 RUNNING_PAGE_PARAM_TRACK_Y,
                                                 RUNNING_PAGE_PARAM_TRACK_WIDTH,
                                                 RUNNING_PAGE_PARAM_TRACK_HEIGHT,
                                                 RUNNING_PAGE_PARAM_TRACK_COLOR,
                                                 RUNNING_PAGE_PARAM_TRACK_RADIUS);
    if (track == NULL) {
        return false;
    }
    lv_obj_add_event_cb(track, running_page_param_event, LV_EVENT_PRESSED, row);
    lv_obj_add_event_cb(track, running_page_param_event, LV_EVENT_PRESSING, row);

    row->fill = running_page_create_progress_segment(track,
                                                     0,
                                                     0,
                                                     1,
                                                     RUNNING_PAGE_PARAM_TRACK_HEIGHT,
                                                     RUNNING_PAGE_PARAM_FILL_COLOR,
                                                     RUNNING_PAGE_PARAM_TRACK_RADIUS);
    if (row->fill == NULL) {
        return false;
    }
    lv_obj_add_event_cb(row->fill, running_page_param_event, LV_EVENT_PRESSED, row);
    lv_obj_add_event_cb(row->fill, running_page_param_event, LV_EVENT_PRESSING, row);

    row->knob = running_page_create_progress_segment(group,
                                                     RUNNING_PAGE_PARAM_TRACK_X,
                                                     RUNNING_PAGE_PARAM_KNOB_Y,
                                                     RUNNING_PAGE_PARAM_KNOB_SIZE,
                                                     RUNNING_PAGE_PARAM_KNOB_SIZE,
                                                     0xD9D9D9,
                                                     RUNNING_PAGE_PARAM_KNOB_SIZE / 2);
    if (row->knob == NULL) {
        return false;
    }
    lv_obj_add_event_cb(row->knob, running_page_param_event, LV_EVENT_PRESSED, row);
    lv_obj_add_event_cb(row->knob, running_page_param_event, LV_EVENT_PRESSING, row);

    max_label = lv_label_create(group);
    if (max_label != NULL) {
        lv_obj_remove_style_all(max_label);
        lv_obj_set_pos(max_label, RUNNING_PAGE_PARAM_MAX_LABEL_X, RUNNING_PAGE_PARAM_MAX_LABEL_Y);
        lv_obj_set_size(max_label, RUNNING_PAGE_PARAM_MAX_LABEL_WIDTH, RUNNING_PAGE_PARAM_MAX_LABEL_HEIGHT);
        lv_obj_set_style_text_color(max_label, lv_color_hex(RUNNING_PAGE_PARAM_FILL_COLOR), LV_PART_MAIN);
        lv_obj_set_style_text_font(max_label, ui_style_font(UI_STYLE_FONT_DETAILS_MENU_VALUE), LV_PART_MAIN);
        lv_obj_set_style_text_align(max_label, LV_TEXT_ALIGN_LEFT, LV_PART_MAIN);
        lv_label_set_text_fmt(max_label, "%d%s", row->max, spec->unit);
    }

    running_page_set_param_value(row, row->value);
    return true;
}

static void running_page_load_recipe_detail(running_page_state_t *state)
{
    ep_simple_recipe_store_t *store = NULL;
    char recipe_db_path[RUNNING_PAGE_SRC_BUFFER_SIZE];

    if (state == NULL || state->recipe_id[0] == '\0') {
        return;
    }

    if (ep_platform_recipe_path(RUNNING_PAGE_RECIPE_DB_NAME, recipe_db_path, sizeof(recipe_db_path)) != EP_OK) {
        return;
    }

    if (ep_simple_recipe_open_saas2_db(recipe_db_path, &store) != EP_OK) {
        return;
    }

    (void)ep_simple_recipe_load_detail(store, state->recipe_id, &state->recipe_detail);
    ep_simple_recipe_close(store);
}

static size_t running_page_count_dynamic_params(const ep_simple_recipe_step_t *step)
{
    size_t count = 0u;
    size_t i;

    if (step == NULL) {
        return 0u;
    }

    for (i = 0u; i < sizeof(running_page_param_specs) / sizeof(running_page_param_specs[0]); ++i) {
        const running_page_param_spec_t *spec = &running_page_param_specs[i];
        const ep_simple_recipe_param_t *param = running_page_find_param(step, spec->key);

        if (running_page_param_is_adjustable(param)) {
            count++;
        }
        if (count >= RUNNING_PAGE_PARAM_MAX_ROWS) {
            break;
        }
    }

    return count;
}

static void running_page_create_dynamic_params(running_page_state_t *state)
{
    const ep_simple_recipe_step_t *step;
    size_t total_row_count;
    size_t i;

    if (state == NULL || state->screen == NULL || state->recipe_detail.step_count == 0u) {
        return;
    }

    step = &state->recipe_detail.steps[0];
    total_row_count = running_page_count_dynamic_params(step);
    for (i = 0u; i < sizeof(running_page_param_specs) / sizeof(running_page_param_specs[0]); ++i) {
        const running_page_param_spec_t *spec = &running_page_param_specs[i];
        const ep_simple_recipe_param_t *param = running_page_find_param(step, spec->key);

        if (!running_page_param_is_adjustable(param)) {
            continue;
        }
        if (state->param_row_count >= RUNNING_PAGE_PARAM_MAX_ROWS) {
            break;
        }
        if (running_page_create_param_row(state->screen,
                                          &state->param_rows[state->param_row_count],
                                          spec,
                                          param,
                                          state->param_row_count,
                                          total_row_count)) {
            state->param_row_count++;
        }
    }
}

static void running_page_apply_recipe_strength(running_page_state_t *state)
{
    const ep_simple_recipe_step_t *step;
    const ep_simple_recipe_param_t *param;
    int32_t strength_value;

    if (state == NULL || state->recipe_detail.step_count == 0u) {
        return;
    }

    step = &state->recipe_detail.steps[0];
    param = running_page_find_param(step, RUNNING_PAGE_PARAM_KEY_COFFEE_POWDER);
    if (!running_page_param_is_adjustable(param) || !running_page_parse_i32(param->ctl_val, &strength_value)) {
        return;
    }

    strength_value = running_page_clamp_i32(strength_value, 1, 3);
    state->strength = (running_page_strength_t)(RUNNING_PAGE_STRENGTH_LIGHT + (strength_value - 1));
    running_page_refresh_strength(state);
}

static uint32_t running_page_recipe_image_scale(const lv_image_header_t *header)
{
    uint32_t max_side;

    if (header == NULL || header->w == 0u || header->h == 0u) {
        return RUNNING_PAGE_IMAGE_SCALE_BASE;
    }

    max_side = header->w > header->h ? header->w : header->h;
    return (RUNNING_PAGE_RECIPE_IMAGE_SIZE * RUNNING_PAGE_IMAGE_SCALE_BASE) / max_side;
}

static uint8_t running_page_pixel_alpha(const lv_draw_buf_t *draw_buf, uint32_t x, uint32_t y)
{
    const uint8_t *pixel;
    uint32_t color_size;
    uint32_t alpha_offset;

    if (draw_buf == NULL || draw_buf->data == NULL) {
        return 0u;
    }

    if (draw_buf->header.cf == LV_COLOR_FORMAT_ARGB8888) {
        pixel = (const uint8_t *)draw_buf->data + y * draw_buf->header.stride + x * sizeof(lv_color32_t);
        return pixel[3];
    }

    if (draw_buf->header.cf == LV_COLOR_FORMAT_XRGB8888 || draw_buf->header.cf == LV_COLOR_FORMAT_RGB888 ||
        draw_buf->header.cf == LV_COLOR_FORMAT_RGB565) {
        return 255u;
    }

    if (draw_buf->header.cf == LV_COLOR_FORMAT_A8) {
        pixel = (const uint8_t *)draw_buf->data + y * draw_buf->header.stride + x;
        return pixel[0];
    }

    if (draw_buf->header.cf == LV_COLOR_FORMAT_RGB565A8) {
        color_size = draw_buf->header.w * draw_buf->header.h * sizeof(lv_color16_t);
        alpha_offset = color_size + y * draw_buf->header.w + x;
        if (alpha_offset < draw_buf->data_size) {
            return ((const uint8_t *)draw_buf->data)[alpha_offset];
        }
    }

    return 255u;
}

static void running_page_recipe_bounds_init(running_page_recipe_bounds_t *bounds)
{
    if (bounds == NULL) {
        return;
    }

    bounds->x1 = UINT32_MAX;
    bounds->y1 = UINT32_MAX;
    bounds->x2 = 0u;
    bounds->y2 = 0u;
    bounds->bottom_anchor_x = 0u;
    bounds->valid = false;
}

static uint32_t running_page_recipe_bottom_anchor_x(const lv_draw_buf_t *draw_buf,
                                                    const running_page_recipe_bounds_t *bounds)
{
    uint32_t band_height;
    uint32_t band_y;
    uint32_t x;
    uint32_t y;
    uint32_t alpha;
    uint64_t weighted_x;
    uint64_t total_alpha;

    if (draw_buf == NULL || bounds == NULL || !bounds->valid || bounds->y2 < bounds->y1) {
        return 0u;
    }

    band_height = (bounds->y2 - bounds->y1 + 1u) / 4u;
    if (band_height < RUNNING_PAGE_RECIPE_ANCHOR_BAND_MIN_HEIGHT) {
        band_height = RUNNING_PAGE_RECIPE_ANCHOR_BAND_MIN_HEIGHT;
    }

    band_y = bounds->y2 >= band_height ? bounds->y2 - band_height + 1u : bounds->y1;
    if (band_y < bounds->y1) {
        band_y = bounds->y1;
    }

    weighted_x = 0u;
    total_alpha = 0u;
    for (y = band_y; y <= bounds->y2; ++y) {
        for (x = bounds->x1; x <= bounds->x2; ++x) {
            alpha = running_page_pixel_alpha(draw_buf, x, y);
            if (alpha <= RUNNING_PAGE_RECIPE_ALPHA_THRESHOLD) {
                continue;
            }
            weighted_x += (uint64_t)x * alpha;
            total_alpha += alpha;
        }
    }

    if (total_alpha == 0u) {
        return (bounds->x1 + bounds->x2 + 1u) / 2u;
    }

    return (uint32_t)(weighted_x / total_alpha);
}

static bool running_page_measure_recipe_bounds(const char *src, running_page_recipe_bounds_t *bounds)
{
    lv_image_decoder_args_t args;
    lv_image_decoder_dsc_t dsc;
    const lv_draw_buf_t *draw_buf;
    uint32_t x;
    uint32_t y;

    if (src == NULL || src[0] == '\0' || bounds == NULL) {
        return false;
    }

    running_page_recipe_bounds_init(bounds);

    args = (lv_image_decoder_args_t){0};
    args.no_cache = true;
    if (lv_image_decoder_open(&dsc, src, &args) != LV_RESULT_OK) {
        return false;
    }

    draw_buf = dsc.decoded;
    if (draw_buf == NULL || draw_buf->data == NULL || draw_buf->header.w == 0u || draw_buf->header.h == 0u) {
        lv_image_decoder_close(&dsc);
        return false;
    }

    for (y = 0u; y < draw_buf->header.h; ++y) {
        for (x = 0u; x < draw_buf->header.w; ++x) {
            if (running_page_pixel_alpha(draw_buf, x, y) <= RUNNING_PAGE_RECIPE_ALPHA_THRESHOLD) {
                continue;
            }

            if (x < bounds->x1) {
                bounds->x1 = x;
            }
            if (y < bounds->y1) {
                bounds->y1 = y;
            }
            if (x > bounds->x2) {
                bounds->x2 = x;
            }
            if (y > bounds->y2) {
                bounds->y2 = y;
            }
            bounds->valid = true;
        }
    }

    if (bounds->valid) {
        bounds->bottom_anchor_x = running_page_recipe_bottom_anchor_x(draw_buf, bounds);
    }

    lv_image_decoder_close(&dsc);
    return bounds->valid;
}

static int32_t running_page_scaled_floor(uint32_t value, uint32_t scale)
{
    return (int32_t)((value * scale) / RUNNING_PAGE_IMAGE_SCALE_BASE);
}

static running_page_recipe_layout_t running_page_recipe_image_layout(const lv_image_header_t *header,
                                                                     const running_page_recipe_bounds_t *bounds)
{
    running_page_recipe_layout_t layout;
    uint32_t visible_bottom_y;

    layout.scale = running_page_recipe_image_scale(header);
    layout.x = RUNNING_PAGE_RECIPE_IMAGE_FALLBACK_X;
    layout.y = RUNNING_PAGE_RECIPE_IMAGE_FALLBACK_Y;

    if (header == NULL || header->w == 0u || header->h == 0u || bounds == NULL || !bounds->valid ||
        bounds->x2 < bounds->x1 || bounds->y2 < bounds->y1) {
        return layout;
    }

    visible_bottom_y = bounds->y2 + 1u;
    layout.x = RUNNING_PAGE_RECIPE_TARGET_CENTER_X + RUNNING_PAGE_RECIPE_TARGET_CENTER_OFFSET_X -
               running_page_scaled_floor(bounds->bottom_anchor_x, layout.scale);
    layout.y = RUNNING_PAGE_RECIPE_TARGET_BOTTOM_Y - running_page_scaled_floor(visible_bottom_y, layout.scale);

    return layout;
}

static void running_page_create_recipe_image(running_page_state_t *state)
{
    lv_image_header_t header;
    lv_obj_t *image;
    running_page_recipe_bounds_t bounds;
    running_page_recipe_layout_t layout;

    if (state == NULL || state->screen == NULL || state->recipe_image_src[0] == '\0') {
        return;
    }

    if (lv_image_decoder_get_info(state->recipe_image_src, &header) != LV_RESULT_OK) {
        return;
    }

    image = lv_image_create(state->screen);
    if (image == NULL) {
        return;
    }

    (void)running_page_measure_recipe_bounds(state->recipe_image_src, &bounds);
    layout = running_page_recipe_image_layout(&header, &bounds);

    lv_image_set_src(image, state->recipe_image_src);
    lv_image_set_pivot(image, 0, 0);
    lv_image_set_scale(image, layout.scale);
    lv_obj_set_pos(image, layout.x, layout.y);
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
    state->strength = RUNNING_PAGE_STRENGTH_DEFAULT;
    running_page_copy_string(state->recipe_image_src,
                             sizeof(state->recipe_image_src),
                             running_page_pending_recipe.image_src);
    running_page_copy_string(state->recipe_id,
                             sizeof(state->recipe_id),
                             running_page_pending_recipe.recipe_id);
    running_page_copy_string(state->recipe_name,
                             sizeof(state->recipe_name),
                             running_page_pending_recipe.recipe_name);
    lv_obj_set_user_data(screen, state);
    settings_common_style_screen(screen);
    running_page_load_recipe_detail(state);
    running_page_create_background(state);
    running_page_create_recipe_title(state);
    if (running_page_has_adjustable_strength(state)) {
        running_page_create_strength_ring(state);
    }
    running_page_create_recipe_image(state);
    running_page_create_start_button(state);
    if (running_page_has_adjustable_strength(state)) {
        running_page_create_strength_controls(state);
        running_page_apply_recipe_strength(state);
    }
    running_page_create_dynamic_params(state);

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
