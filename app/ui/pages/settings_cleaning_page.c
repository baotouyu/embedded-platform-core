#include "pages/settings_page.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "lvgl.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>

#define SETTINGS_CLEANING_TITLE_TEXT "清洗"
#define SETTINGS_CLEANING_HEADER_HEIGHT 96
#define SETTINGS_CLEANING_TITLE_X 344
#define SETTINGS_CLEANING_TITLE_Y 36
#define SETTINGS_CLEANING_TITLE_WIDTH 112
#define SETTINGS_CLEANING_TITLE_HEIGHT 48

#define SETTINGS_CLEANING_MENU_WIDTH 240
#define SETTINGS_CLEANING_MENU_Y SETTINGS_CLEANING_HEADER_HEIGHT
#define SETTINGS_CLEANING_MENU_HEIGHT (SETTINGS_PAGE_SCREEN_HEIGHT - SETTINGS_CLEANING_MENU_Y)
#define SETTINGS_CLEANING_MENU_ITEM_COUNT 3u
#define SETTINGS_CLEANING_MENU_ROW_HEIGHT 64
#define SETTINGS_CLEANING_MENU_SELECTED_COLOR 0x000000
#define SETTINGS_CLEANING_MENU_UNSELECTED_COLOR SETTINGS_PAGE_BUTTON_COLOR
#define SETTINGS_CLEANING_MENU_FILL_COLOR SETTINGS_PAGE_BUTTON_COLOR
#define SETTINGS_CLEANING_MENU_SEPARATOR_COLOR 0x3A3A3A
#define SETTINGS_CLEANING_MENU_LABEL_X 32
#define SETTINGS_CLEANING_MENU_LABEL_Y 20
#define SETTINGS_CLEANING_MENU_LABEL_WIDTH 176
#define SETTINGS_CLEANING_MENU_LABEL_HEIGHT 28

#define SETTINGS_CLEANING_CONTENT_X SETTINGS_CLEANING_MENU_WIDTH
#define SETTINGS_CLEANING_CONTENT_Y SETTINGS_CLEANING_HEADER_HEIGHT
#define SETTINGS_CLEANING_CONTENT_WIDTH 560
#define SETTINGS_CLEANING_CONTENT_HEIGHT 384
#define SETTINGS_CLEANING_CONTENT_PAD_X 28
#define SETTINGS_CLEANING_CONTENT_PAD_TOP 14

#define SETTINGS_CLEANING_CARD_WIDTH 496
#define SETTINGS_CLEANING_CARD_HEIGHT 72
#define SETTINGS_CLEANING_CARD_RADIUS 12
#define SETTINGS_CLEANING_CARD_GAP_Y 18
#define SETTINGS_CLEANING_CARD_ICON_NAME "settings_icon_clean.png"
#define SETTINGS_CLEANING_MAINTENANCE_DESCALING_ICON_NAME "settings_details_descaling_icon.png"
#define SETTINGS_CLEANING_DESCALING_ICON_NAME "settings_cleaning_descaling_icon.png"
#define SETTINGS_CLEANING_CARD_ICON_SIZE 48
#define SETTINGS_CLEANING_CARD_ICON_X 24
#define SETTINGS_CLEANING_CARD_ICON_Y 12
#define SETTINGS_CLEANING_CARD_TEXT_X 96
#define SETTINGS_CLEANING_CARD_TEXT_Y 23
#define SETTINGS_CLEANING_CARD_TEXT_WIDTH 250
#define SETTINGS_CLEANING_CARD_TEXT_HEIGHT 28
#define SETTINGS_CLEANING_ACTION_BUTTON_WIDTH 112
#define SETTINGS_CLEANING_ACTION_BUTTON_HEIGHT 48
#define SETTINGS_CLEANING_ACTION_BUTTON_X 360
#define SETTINGS_CLEANING_ACTION_BUTTON_Y 12
#define SETTINGS_CLEANING_ACTION_BUTTON_RADIUS 24
#define SETTINGS_CLEANING_ACTION_BUTTON_COLOR 0xB56A2E

#define SETTINGS_CLEANING_LEVEL_LABEL_X 72
#define SETTINGS_CLEANING_LEVEL_LABEL_Y 14
#define SETTINGS_CLEANING_LEVEL_VALUE_X 208
#define SETTINGS_CLEANING_LEVEL_VALUE_Y 14
#define SETTINGS_CLEANING_LEVEL_GROUP_X 72
#define SETTINGS_CLEANING_LEVEL_GROUP_Y 62
#define SETTINGS_CLEANING_LEVEL_GROUP_WIDTH 416
#define SETTINGS_CLEANING_LEVEL_GROUP_HEIGHT 32
#define SETTINGS_CLEANING_LEVEL_ICON_AREA_WIDTH 44
#define SETTINGS_CLEANING_LEVEL_ICON_X 0
#define SETTINGS_CLEANING_LEVEL_ICON_Y 0
#define SETTINGS_CLEANING_LEVEL_ICON_SIZE 32
#define SETTINGS_CLEANING_LEVEL_TRACK_X SETTINGS_CLEANING_LEVEL_ICON_AREA_WIDTH
#define SETTINGS_CLEANING_LEVEL_TRACK_Y 11
#define SETTINGS_CLEANING_LEVEL_TRACK_WIDTH 304
#define SETTINGS_CLEANING_LEVEL_TRACK_HEIGHT 10
#define SETTINGS_CLEANING_LEVEL_TRACK_RADIUS 5
#define SETTINGS_CLEANING_LEVEL_KNOB_SIZE 30
#define SETTINGS_CLEANING_LEVEL_KNOB_Y 1
#define SETTINGS_CLEANING_LEVEL_MIN 1
#define SETTINGS_CLEANING_LEVEL_MAX 5
#define SETTINGS_CLEANING_LEVEL_VALUE 2
#define SETTINGS_CLEANING_LEVEL_PROGRESS_WIDTH \
    ((SETTINGS_CLEANING_LEVEL_TRACK_WIDTH * (SETTINGS_CLEANING_LEVEL_VALUE - SETTINGS_CLEANING_LEVEL_MIN)) / \
     (SETTINGS_CLEANING_LEVEL_MAX - SETTINGS_CLEANING_LEVEL_MIN))
#define SETTINGS_CLEANING_LEVEL_KNOB_X \
    (SETTINGS_CLEANING_LEVEL_TRACK_X + SETTINGS_CLEANING_LEVEL_PROGRESS_WIDTH - (SETTINGS_CLEANING_LEVEL_KNOB_SIZE / 2))
#define SETTINGS_CLEANING_LEVEL_MAX_LABEL_X \
    (SETTINGS_CLEANING_LEVEL_ICON_AREA_WIDTH + SETTINGS_CLEANING_LEVEL_TRACK_WIDTH)
#define SETTINGS_CLEANING_LEVEL_MAX_LABEL_Y 2
#define SETTINGS_CLEANING_LEVEL_MAX_LABEL_WIDTH 68
#define SETTINGS_CLEANING_LEVEL_MAX_LABEL_HEIGHT 28
#define SETTINGS_CLEANING_LEVEL_GOLD_COLOR 0xD09A6A

typedef enum {
    SETTINGS_CLEANING_TAB_DAILY = 0,
    SETTINGS_CLEANING_TAB_MAINTENANCE,
    SETTINGS_CLEANING_TAB_DESCALING_LEVEL,
} settings_cleaning_tab_t;

typedef struct {
    const char *title;
    settings_cleaning_tab_t tab;
} settings_cleaning_menu_item_t;

typedef struct {
    const char *title;
    const char *button_text;
    const char *icon_name;
} settings_cleaning_action_item_t;

typedef struct {
    lv_obj_t *screen;
    lv_obj_t *content;
    lv_obj_t *menu_rows[SETTINGS_CLEANING_MENU_ITEM_COUNT];
    lv_obj_t *menu_titles[SETTINGS_CLEANING_MENU_ITEM_COUNT];
    lv_obj_t *descaling_progress_group;
    lv_obj_t *descaling_progress_fill;
    lv_obj_t *descaling_knob;
    lv_obj_t *descaling_value_label;
    int32_t descaling_level;
    settings_cleaning_tab_t selected_tab;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char icon_src[8][SETTINGS_PAGE_SRC_BUFFER_SIZE];
} settings_cleaning_page_state_t;

static const settings_cleaning_menu_item_t settings_cleaning_menu_items[] = {
    {"日常清洗", SETTINGS_CLEANING_TAB_DAILY},
    {"机器维护清洁", SETTINGS_CLEANING_TAB_MAINTENANCE},
    {"除垢等级", SETTINGS_CLEANING_TAB_DESCALING_LEVEL},
};

static const settings_cleaning_action_item_t settings_cleaning_daily_items[] = {
    {"冲泡器简易清洗", "清洗", SETTINGS_CLEANING_CARD_ICON_NAME},
    {"奶泡器简易清洗", "清洗", SETTINGS_CLEANING_CARD_ICON_NAME},
    {"奶泡器深度清洗", "立即除垢", SETTINGS_CLEANING_CARD_ICON_NAME},
};

static const settings_cleaning_action_item_t settings_cleaning_maintenance_items[] = {
    {"冲泡器深度清洁（加药片）", "清洗", SETTINGS_CLEANING_CARD_ICON_NAME},
    {"奶泡器深度清洁（加药片）", "清洗", SETTINGS_CLEANING_CARD_ICON_NAME},
    {"除垢", "立即除垢", SETTINGS_CLEANING_MAINTENANCE_DESCALING_ICON_NAME},
};

static void settings_cleaning_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static void settings_cleaning_clear_content(settings_cleaning_page_state_t *state)
{
    if (state == NULL || state->content == NULL) {
        return;
    }

    state->descaling_progress_group = NULL;
    state->descaling_progress_fill = NULL;
    state->descaling_knob = NULL;
    state->descaling_value_label = NULL;
    lv_obj_clean(state->content);
    lv_obj_clear_flag(state->content, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_scrollbar_mode(state->content, LV_SCROLLBAR_MODE_OFF);
}

static lv_obj_t *settings_cleaning_create_label(lv_obj_t *parent,
                                                const char *text,
                                                int32_t x,
                                                int32_t y,
                                                int32_t width,
                                                int32_t height,
                                                ui_style_font_id_t font,
                                                lv_text_align_t align)
{
    lv_obj_t *label;

    label = lv_label_create(parent);
    if (label == NULL) {
        return NULL;
    }

    lv_obj_remove_style_all(label);
    lv_obj_set_size(label, width, height);
    lv_obj_set_pos(label, x, y);
    lv_obj_set_style_text_color(label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(label, ui_style_font(font), LV_PART_MAIN);
    lv_obj_set_style_text_align(label, align, LV_PART_MAIN);
    lv_label_set_long_mode(label, LV_LABEL_LONG_CLIP);
    lv_label_set_text(label, text);

    return label;
}

static lv_obj_t *settings_cleaning_create_gold_label(lv_obj_t *parent,
                                                     const char *text,
                                                     int32_t x,
                                                     int32_t y,
                                                     int32_t width,
                                                     int32_t height,
                                                     ui_style_font_id_t font,
                                                     lv_text_align_t align)
{
    lv_obj_t *label;

    label = settings_cleaning_create_label(parent, text, x, y, width, height, font, align);
    if (label != NULL) {
        lv_obj_set_style_text_color(label, lv_color_hex(SETTINGS_CLEANING_LEVEL_GOLD_COLOR), LV_PART_MAIN);
    }

    return label;
}

static bool settings_cleaning_create_title(settings_cleaning_page_state_t *state)
{
    return settings_cleaning_create_label(state->screen,
                                          SETTINGS_CLEANING_TITLE_TEXT,
                                          SETTINGS_CLEANING_TITLE_X,
                                          SETTINGS_CLEANING_TITLE_Y,
                                          SETTINGS_CLEANING_TITLE_WIDTH,
                                          SETTINGS_CLEANING_TITLE_HEIGHT,
                                          UI_STYLE_FONT_HOME_USER,
                                          LV_TEXT_ALIGN_CENTER) != NULL;
}

static bool settings_cleaning_create_action_button(lv_obj_t *parent, const char *text)
{
    lv_obj_t *button;

    button = lv_button_create(parent);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_CLEANING_ACTION_BUTTON_WIDTH, SETTINGS_CLEANING_ACTION_BUTTON_HEIGHT);
    lv_obj_set_pos(button, SETTINGS_CLEANING_ACTION_BUTTON_X, SETTINGS_CLEANING_ACTION_BUTTON_Y);
    lv_obj_set_style_bg_color(button, lv_color_hex(SETTINGS_CLEANING_ACTION_BUTTON_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(button, SETTINGS_CLEANING_ACTION_BUTTON_RADIUS, LV_PART_MAIN);
    lv_obj_clear_flag(button, LV_OBJ_FLAG_SCROLLABLE);

    return settings_cleaning_create_label(button,
                                          text,
                                          0,
                                          12,
                                          SETTINGS_CLEANING_ACTION_BUTTON_WIDTH,
                                          28,
                                          UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                          LV_TEXT_ALIGN_CENTER) != NULL;
}

static bool settings_cleaning_load_icon(settings_cleaning_page_state_t *state,
                                        const char *icon_name,
                                        size_t image_index)
{
    return image_index < sizeof(state->icon_src) / sizeof(state->icon_src[0]) &&
           ep_platform_lvgl_image_src(icon_name, state->icon_src[image_index], sizeof(state->icon_src[image_index])) ==
               EP_OK;
}

static bool settings_cleaning_create_clean_card(settings_cleaning_page_state_t *state,
                                                const settings_cleaning_action_item_t *item,
                                                size_t index)
{
    lv_obj_t *card;
    lv_obj_t *image;
    int32_t y;

    y = SETTINGS_CLEANING_CONTENT_PAD_TOP +
        (int32_t)index * (SETTINGS_CLEANING_CARD_HEIGHT + SETTINGS_CLEANING_CARD_GAP_Y);

    card = lv_obj_create(state->content);
    if (card == NULL) {
        return false;
    }

    lv_obj_remove_style_all(card);
    lv_obj_set_size(card, SETTINGS_CLEANING_CARD_WIDTH, SETTINGS_CLEANING_CARD_HEIGHT);
    lv_obj_set_pos(card, SETTINGS_CLEANING_CONTENT_PAD_X, y);
    lv_obj_set_style_bg_color(card, lv_color_hex(SETTINGS_PAGE_BUTTON_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(card, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(card, SETTINGS_CLEANING_CARD_RADIUS, LV_PART_MAIN);
    lv_obj_clear_flag(card, LV_OBJ_FLAG_SCROLLABLE);

    if (settings_cleaning_load_icon(state, item->icon_name, index)) {
        image = lv_image_create(card);
        if (image != NULL) {
            lv_obj_remove_style_all(image);
            lv_obj_set_size(image, SETTINGS_CLEANING_CARD_ICON_SIZE, SETTINGS_CLEANING_CARD_ICON_SIZE);
            lv_obj_set_pos(image, SETTINGS_CLEANING_CARD_ICON_X, SETTINGS_CLEANING_CARD_ICON_Y);
            lv_image_set_src(image, state->icon_src[index]);
        }
    }

    return settings_cleaning_create_label(card,
                                          item->title,
                                          SETTINGS_CLEANING_CARD_TEXT_X,
                                          SETTINGS_CLEANING_CARD_TEXT_Y,
                                          SETTINGS_CLEANING_CARD_TEXT_WIDTH,
                                          SETTINGS_CLEANING_CARD_TEXT_HEIGHT,
                                          UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                          LV_TEXT_ALIGN_LEFT) != NULL &&
           settings_cleaning_create_action_button(card, item->button_text);
}

static bool settings_cleaning_create_daily_clean(settings_cleaning_page_state_t *state)
{
    settings_cleaning_clear_content(state);

    for (size_t i = 0u; i < sizeof(settings_cleaning_daily_items) / sizeof(settings_cleaning_daily_items[0]); ++i) {
        if (!settings_cleaning_create_clean_card(state, &settings_cleaning_daily_items[i], i)) {
            return false;
        }
    }

    return true;
}

static bool settings_cleaning_create_maintenance_clean(settings_cleaning_page_state_t *state)
{
    settings_cleaning_clear_content(state);

    for (size_t i = 0u;
         i < sizeof(settings_cleaning_maintenance_items) / sizeof(settings_cleaning_maintenance_items[0]);
         ++i) {
        if (!settings_cleaning_create_clean_card(state, &settings_cleaning_maintenance_items[i], i)) {
            return false;
        }
    }

    return true;
}

static int32_t settings_cleaning_progress_width_for_level(int32_t level)
{
    if (level < SETTINGS_CLEANING_LEVEL_MIN) {
        level = SETTINGS_CLEANING_LEVEL_MIN;
    } else if (level > SETTINGS_CLEANING_LEVEL_MAX) {
        level = SETTINGS_CLEANING_LEVEL_MAX;
    }

    return (SETTINGS_CLEANING_LEVEL_TRACK_WIDTH * (level - SETTINGS_CLEANING_LEVEL_MIN)) /
           (SETTINGS_CLEANING_LEVEL_MAX - SETTINGS_CLEANING_LEVEL_MIN);
}

static int32_t settings_cleaning_knob_x_for_level(int32_t level)
{
    return SETTINGS_CLEANING_LEVEL_TRACK_X + settings_cleaning_progress_width_for_level(level) -
           (SETTINGS_CLEANING_LEVEL_KNOB_SIZE / 2);
}

static int32_t settings_cleaning_level_for_point(settings_cleaning_page_state_t *state, const lv_point_t *point)
{
    lv_area_t group_coords;
    int32_t relative_x;
    int32_t level_step;

    if (state == NULL || state->descaling_progress_group == NULL || point == NULL) {
        return SETTINGS_CLEANING_LEVEL_MIN;
    }

    lv_obj_get_coords(state->descaling_progress_group, &group_coords);
    relative_x = point->x - group_coords.x1 - SETTINGS_CLEANING_LEVEL_TRACK_X;
    if (relative_x <= 0) {
        return SETTINGS_CLEANING_LEVEL_MIN;
    }
    if (relative_x >= SETTINGS_CLEANING_LEVEL_TRACK_WIDTH) {
        return SETTINGS_CLEANING_LEVEL_MAX;
    }

    level_step = (relative_x * (SETTINGS_CLEANING_LEVEL_MAX - SETTINGS_CLEANING_LEVEL_MIN) +
                  (SETTINGS_CLEANING_LEVEL_TRACK_WIDTH / 2)) /
                 SETTINGS_CLEANING_LEVEL_TRACK_WIDTH;
    return SETTINGS_CLEANING_LEVEL_MIN + level_step;
}

static void settings_cleaning_set_descaling_level(settings_cleaning_page_state_t *state, int32_t level)
{
    int32_t progress_width;

    if (state == NULL) {
        return;
    }

    if (level < SETTINGS_CLEANING_LEVEL_MIN) {
        level = SETTINGS_CLEANING_LEVEL_MIN;
    } else if (level > SETTINGS_CLEANING_LEVEL_MAX) {
        level = SETTINGS_CLEANING_LEVEL_MAX;
    }

    state->descaling_level = level;
    progress_width = settings_cleaning_progress_width_for_level(level);

    if (state->descaling_progress_fill != NULL) {
        lv_obj_set_width(state->descaling_progress_fill, progress_width);
    }
    if (state->descaling_knob != NULL) {
        lv_obj_set_x(state->descaling_knob, settings_cleaning_knob_x_for_level(level));
    }
    if (state->descaling_value_label != NULL) {
        lv_label_set_text_fmt(state->descaling_value_label, "%d级", state->descaling_level);
    }
}

static void settings_cleaning_descaling_progress_event(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;
    lv_point_t point;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL) {
        return;
    }

    lv_indev_get_point(lv_indev_active(), &point);
    settings_cleaning_set_descaling_level(state, settings_cleaning_level_for_point(state, &point));
}

static lv_obj_t *settings_cleaning_create_descaling_progress_group(lv_obj_t *parent)
{
    lv_obj_t *group;

    group = lv_obj_create(parent);
    if (group == NULL) {
        return NULL;
    }

    lv_obj_remove_style_all(group);
    lv_obj_set_size(group, SETTINGS_CLEANING_LEVEL_GROUP_WIDTH, SETTINGS_CLEANING_LEVEL_GROUP_HEIGHT);
    lv_obj_set_pos(group, SETTINGS_CLEANING_LEVEL_GROUP_X, SETTINGS_CLEANING_LEVEL_GROUP_Y);
    lv_obj_set_style_bg_opa(group, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(group, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(group, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(group, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(group, LV_OBJ_FLAG_CLICKABLE);

    return group;
}

static lv_obj_t *settings_cleaning_create_progress_segment(lv_obj_t *parent,
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

static bool settings_cleaning_create_descaling_progress(settings_cleaning_page_state_t *state)
{
    lv_obj_t *group;
    lv_obj_t *image;
    lv_obj_t *track;
    lv_obj_t *knob;
    size_t image_index = 0u;

    if (state == NULL || state->content == NULL) {
        return false;
    }

    group = settings_cleaning_create_descaling_progress_group(state->content);
    if (group == NULL) {
        return false;
    }
    state->descaling_progress_group = group;
    lv_obj_add_event_cb(group, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(group, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSING, state);

    if (settings_cleaning_load_icon(state, SETTINGS_CLEANING_DESCALING_ICON_NAME, image_index)) {
        image = lv_image_create(group);
        if (image != NULL) {
            lv_obj_remove_style_all(image);
            lv_obj_set_size(image, SETTINGS_CLEANING_LEVEL_ICON_SIZE, SETTINGS_CLEANING_LEVEL_ICON_SIZE);
            lv_obj_set_pos(image, SETTINGS_CLEANING_LEVEL_ICON_X, SETTINGS_CLEANING_LEVEL_ICON_Y);
            lv_image_set_src(image, state->icon_src[image_index]);
        }
    }

    track = settings_cleaning_create_progress_segment(group,
                                                      SETTINGS_CLEANING_LEVEL_TRACK_X,
                                                      SETTINGS_CLEANING_LEVEL_TRACK_Y,
                                                      SETTINGS_CLEANING_LEVEL_TRACK_WIDTH,
                                                      SETTINGS_CLEANING_LEVEL_TRACK_HEIGHT,
                                                      SETTINGS_SHARED_GRAY_BORDER_COLOR,
                                                      SETTINGS_CLEANING_LEVEL_TRACK_RADIUS);
    if (track == NULL) {
        return false;
    }
    lv_obj_add_event_cb(track, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(track, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSING, state);

    state->descaling_progress_fill = settings_cleaning_create_progress_segment(track,
                                                                               0,
                                                                               0,
                                                                               SETTINGS_CLEANING_LEVEL_PROGRESS_WIDTH,
                                                                               SETTINGS_CLEANING_LEVEL_TRACK_HEIGHT,
                                                                               SETTINGS_CLEANING_LEVEL_GOLD_COLOR,
                                                                               SETTINGS_CLEANING_LEVEL_TRACK_RADIUS);
    if (state->descaling_progress_fill == NULL) {
        return false;
    }
    lv_obj_add_event_cb(state->descaling_progress_fill, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(state->descaling_progress_fill, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSING, state);

    knob = settings_cleaning_create_progress_segment(group,
                                                     SETTINGS_CLEANING_LEVEL_KNOB_X,
                                                     SETTINGS_CLEANING_LEVEL_KNOB_Y,
                                                     SETTINGS_CLEANING_LEVEL_KNOB_SIZE,
                                                     SETTINGS_CLEANING_LEVEL_KNOB_SIZE,
                                                     SETTINGS_PAGE_TEXT_COLOR,
                                                     SETTINGS_CLEANING_LEVEL_KNOB_SIZE / 2);
    if (knob == NULL) {
        return false;
    }
    state->descaling_knob = knob;
    lv_obj_add_event_cb(knob, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(knob, settings_cleaning_descaling_progress_event, LV_EVENT_PRESSING, state);

    if (settings_cleaning_create_gold_label(group,
                                            "5级",
                                            SETTINGS_CLEANING_LEVEL_MAX_LABEL_X,
                                            SETTINGS_CLEANING_LEVEL_MAX_LABEL_Y,
                                            SETTINGS_CLEANING_LEVEL_MAX_LABEL_WIDTH,
                                            SETTINGS_CLEANING_LEVEL_MAX_LABEL_HEIGHT,
                                            UI_STYLE_FONT_DETAILS_MENU_VALUE,
                                            LV_TEXT_ALIGN_CENTER) == NULL) {
        return false;
    }

    settings_cleaning_set_descaling_level(state, state->descaling_level);
    return true;
}

static bool settings_cleaning_create_descaling_level(settings_cleaning_page_state_t *state)
{
    settings_cleaning_clear_content(state);

    if (settings_cleaning_create_label(state->content,
                                       "除垢等级",
                                       SETTINGS_CLEANING_LEVEL_LABEL_X,
                                       SETTINGS_CLEANING_LEVEL_LABEL_Y,
                                       100,
                                       28,
                                       UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                       LV_TEXT_ALIGN_LEFT) == NULL ||
        (state->descaling_value_label = settings_cleaning_create_label(state->content,
                                                                       "2级",
                                                                       SETTINGS_CLEANING_LEVEL_VALUE_X,
                                                                       SETTINGS_CLEANING_LEVEL_VALUE_Y,
                                                                       48,
                                                                       28,
                                                                       UI_STYLE_FONT_HOME_SIDE,
                                                                       LV_TEXT_ALIGN_CENTER)) == NULL ||
        !settings_cleaning_create_descaling_progress(state)) {
        return false;
    }

    return true;
}

static bool settings_cleaning_create_content_for_tab(settings_cleaning_page_state_t *state)
{
    switch (state->selected_tab) {
    case SETTINGS_CLEANING_TAB_DAILY:
        return settings_cleaning_create_daily_clean(state);
    case SETTINGS_CLEANING_TAB_MAINTENANCE:
        return settings_cleaning_create_maintenance_clean(state);
    case SETTINGS_CLEANING_TAB_DESCALING_LEVEL:
        return settings_cleaning_create_descaling_level(state);
    default:
        return false;
    }
}

static void settings_cleaning_refresh_menu(settings_cleaning_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    for (size_t i = 0u; i < SETTINGS_CLEANING_MENU_ITEM_COUNT; ++i) {
        bool selected = settings_cleaning_menu_items[i].tab == state->selected_tab;

        if (state->menu_rows[i] != NULL) {
            lv_obj_set_style_bg_color(
                state->menu_rows[i],
                lv_color_hex(selected ? SETTINGS_CLEANING_MENU_SELECTED_COLOR : SETTINGS_CLEANING_MENU_UNSELECTED_COLOR),
                LV_PART_MAIN);
            lv_obj_set_style_bg_opa(state->menu_rows[i], LV_OPA_COVER, LV_PART_MAIN);
        }
    }
}

static void settings_cleaning_menu_row_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;
    lv_obj_t *target;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    target = lv_event_get_current_target_obj(event);
    if (state == NULL || target == NULL) {
        return;
    }

    for (size_t i = 0u; i < SETTINGS_CLEANING_MENU_ITEM_COUNT; ++i) {
        if (state->menu_rows[i] == target || state->menu_titles[i] == target) {
            state->selected_tab = settings_cleaning_menu_items[i].tab;
            settings_cleaning_refresh_menu(state);
            (void)settings_cleaning_create_content_for_tab(state);
            return;
        }
    }
}

static bool settings_cleaning_create_menu(settings_cleaning_page_state_t *state)
{
    lv_obj_t *menu;
    lv_obj_t *fill;

    menu = lv_obj_create(state->screen);
    if (menu == NULL) {
        return false;
    }

    lv_obj_remove_style_all(menu);
    lv_obj_set_size(menu, SETTINGS_CLEANING_MENU_WIDTH, SETTINGS_CLEANING_MENU_HEIGHT);
    lv_obj_set_pos(menu, 0, SETTINGS_CLEANING_MENU_Y);
    lv_obj_set_style_bg_color(menu, lv_color_hex(SETTINGS_CLEANING_MENU_FILL_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(menu, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(menu, LV_OBJ_FLAG_SCROLLABLE);

    for (size_t i = 0u; i < SETTINGS_CLEANING_MENU_ITEM_COUNT; ++i) {
        lv_obj_t *row;
        int32_t y = (int32_t)i * SETTINGS_CLEANING_MENU_ROW_HEIGHT;

        row = lv_obj_create(menu);
        if (row == NULL) {
            return false;
        }

        state->menu_rows[i] = row;
        lv_obj_remove_style_all(row);
        lv_obj_set_size(row, SETTINGS_CLEANING_MENU_WIDTH, SETTINGS_CLEANING_MENU_ROW_HEIGHT);
        lv_obj_set_pos(row, 0, y);
        lv_obj_set_style_border_color(row, lv_color_hex(SETTINGS_CLEANING_MENU_SEPARATOR_COLOR), LV_PART_MAIN);
        lv_obj_set_style_border_width(row, i + 1u == SETTINGS_CLEANING_MENU_ITEM_COUNT ? 0 : 1, LV_PART_MAIN);
        lv_obj_set_style_border_side(row, LV_BORDER_SIDE_BOTTOM, LV_PART_MAIN);
        lv_obj_clear_flag(row, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(row, settings_cleaning_menu_row_clicked, LV_EVENT_CLICKED, state);

        state->menu_titles[i] = settings_cleaning_create_label(row,
                                                               settings_cleaning_menu_items[i].title,
                                                               SETTINGS_CLEANING_MENU_LABEL_X,
                                                               SETTINGS_CLEANING_MENU_LABEL_Y,
                                                               SETTINGS_CLEANING_MENU_LABEL_WIDTH,
                                                               SETTINGS_CLEANING_MENU_LABEL_HEIGHT,
                                                               UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                                               LV_TEXT_ALIGN_LEFT);
        if (state->menu_titles[i] == NULL) {
            return false;
        }
        lv_obj_add_flag(state->menu_titles[i], LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(state->menu_titles[i], settings_cleaning_menu_row_clicked, LV_EVENT_CLICKED, state);
    }

    fill = lv_obj_create(menu);
    if (fill == NULL) {
        return false;
    }

    lv_obj_remove_style_all(fill);
    lv_obj_set_size(fill,
                    SETTINGS_CLEANING_MENU_WIDTH,
                    SETTINGS_CLEANING_MENU_HEIGHT -
                        (SETTINGS_CLEANING_MENU_ROW_HEIGHT * SETTINGS_CLEANING_MENU_ITEM_COUNT));
    lv_obj_set_pos(fill, 0, SETTINGS_CLEANING_MENU_ROW_HEIGHT * SETTINGS_CLEANING_MENU_ITEM_COUNT);
    lv_obj_set_style_bg_color(fill, lv_color_hex(SETTINGS_CLEANING_MENU_FILL_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(fill, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(fill, LV_OBJ_FLAG_SCROLLABLE);

    settings_cleaning_refresh_menu(state);
    return true;
}

static bool settings_cleaning_create_content(settings_cleaning_page_state_t *state)
{
    state->content = lv_obj_create(state->screen);
    if (state->content == NULL) {
        return false;
    }

    lv_obj_remove_style_all(state->content);
    lv_obj_set_size(state->content, SETTINGS_CLEANING_CONTENT_WIDTH, SETTINGS_CLEANING_CONTENT_HEIGHT);
    lv_obj_set_pos(state->content, SETTINGS_CLEANING_CONTENT_X, SETTINGS_CLEANING_CONTENT_Y);
    lv_obj_set_style_bg_color(state->content, lv_color_hex(SETTINGS_PAGE_BG_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(state->content, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_opa(state->content, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(state->content, LV_OPA_TRANSP, LV_PART_MAIN);

    return settings_cleaning_create_content_for_tab(state);
}

void settings_cleaning_page_destroy(page_manager_page_ctx_t *ctx)
{
    settings_cleaning_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (settings_cleaning_page_state_t *)lv_obj_get_user_data(ctx->screen);
    free(state);
}

lv_obj_t *settings_cleaning_page_create(page_manager_page_ctx_t *ctx)
{
    lv_obj_t *screen;
    settings_cleaning_page_state_t *state;

    (void)ctx;

    state = (settings_cleaning_page_state_t *)calloc(1u, sizeof(*state));
    if (state == NULL) {
        return NULL;
    }

    screen = lv_obj_create(NULL);
    if (screen == NULL) {
        free(state);
        return NULL;
    }

    state->screen = screen;
    state->selected_tab = SETTINGS_CLEANING_TAB_DAILY;
    state->descaling_level = SETTINGS_CLEANING_LEVEL_VALUE;
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
                                            settings_cleaning_back_clicked) ||
        !settings_cleaning_create_title(state) ||
        !settings_cleaning_create_menu(state) ||
        !settings_cleaning_create_content(state)) {
        lv_obj_delete(screen);
        free(state);
        return NULL;
    }

    return screen;
}

void settings_cleaning_page_event(page_manager_page_ctx_t *ctx,
                                  uint32_t code,
                                  uint32_t wparam,
                                  uint32_t lparam)
{
    (void)ctx;
    (void)code;
    (void)wparam;
    (void)lparam;
}
