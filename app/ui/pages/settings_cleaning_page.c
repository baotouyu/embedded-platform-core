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

#define SETTINGS_CLEANING_RINSE_DURATION_MS 10000u
#define SETTINGS_CLEANING_RINSE_TICK_MS 1000u
#define SETTINGS_CLEANING_RINSE_RETURN_DELAY_MS 1000u
#define SETTINGS_CLEANING_RINSE_COMPLETE_ICON_NAME "Frame-2.png"
#define SETTINGS_CLEANING_RINSE_INTERRUPTED_ICON_NAME "Frame-3.png"
#define SETTINGS_CLEANING_RINSE_PAGE_WIDTH SETTINGS_PAGE_SCREEN_WIDTH
#define SETTINGS_CLEANING_RINSE_PAGE_HEIGHT SETTINGS_PAGE_SCREEN_HEIGHT
#define SETTINGS_CLEANING_RINSE_BUTTON_WIDTH 236
#define SETTINGS_CLEANING_RINSE_BUTTON_HEIGHT 74
#define SETTINGS_CLEANING_RINSE_BUTTON_X 482
#define SETTINGS_CLEANING_RINSE_BUTTON_Y 203
#define SETTINGS_CLEANING_RINSE_BUTTON_RADIUS 37
#define SETTINGS_CLEANING_RINSE_BUTTON_LABEL_X 34
#define SETTINGS_CLEANING_RINSE_BUTTON_LABEL_Y 16
#define SETTINGS_CLEANING_RINSE_BUTTON_LABEL_WIDTH 132
#define SETTINGS_CLEANING_RINSE_BUTTON_LABEL_HEIGHT 42
#define SETTINGS_CLEANING_RINSE_RUNNING_LABEL_X 0
#define SETTINGS_CLEANING_RINSE_RUNNING_LABEL_WIDTH SETTINGS_CLEANING_RINSE_BUTTON_WIDTH
#define SETTINGS_CLEANING_RINSE_HELPER_X 540
#define SETTINGS_CLEANING_RINSE_HELPER_Y 139
#define SETTINGS_CLEANING_RINSE_HELPER_WIDTH 120
#define SETTINGS_CLEANING_RINSE_HELPER_HEIGHT 32
#define SETTINGS_CLEANING_RINSE_STATUS_ICON_SIZE 32
#define SETTINGS_CLEANING_RINSE_STATUS_ICON_X 168
#define SETTINGS_CLEANING_RINSE_STATUS_ICON_Y 20

#define SETTINGS_CLEANING_PREPARE_PAGE_WIDTH SETTINGS_PAGE_SCREEN_WIDTH
#define SETTINGS_CLEANING_PREPARE_PAGE_HEIGHT SETTINGS_PAGE_SCREEN_HEIGHT
#define SETTINGS_CLEANING_PREPARE_ICON_BOX_WIDTH 240
#define SETTINGS_CLEANING_PREPARE_ICON_BOX_HEIGHT 240
#define SETTINGS_CLEANING_PREPARE_ICON_BOX_X 56
#define SETTINGS_CLEANING_PREPARE_ICON_BOX_Y 117
#define SETTINGS_CLEANING_PREPARE_ICON_NAME "Frame-4.png"
#define SETTINGS_CLEANING_PREPARE_PANEL_WIDTH 416
#define SETTINGS_CLEANING_PREPARE_PANEL_HEIGHT 376
#define SETTINGS_CLEANING_PREPARE_PANEL_X 336
#define SETTINGS_CLEANING_PREPARE_PANEL_Y 52
#define SETTINGS_CLEANING_PREPARE_PROMPT_WIDTH 264
#define SETTINGS_CLEANING_PREPARE_PROMPT_HEIGHT 64
#define SETTINGS_CLEANING_PREPARE_PROMPT_X 76
#define SETTINGS_CLEANING_PREPARE_PROMPT_Y 25
#define SETTINGS_CLEANING_PREPARE_TIME_LABEL_X 0
#define SETTINGS_CLEANING_PREPARE_TIME_LABEL_Y 172
#define SETTINGS_CLEANING_PREPARE_TIME_LABEL_WIDTH 100
#define SETTINGS_CLEANING_PREPARE_TIME_LABEL_HEIGHT 32
#define SETTINGS_CLEANING_PREPARE_TIME_VALUE_X 170
#define SETTINGS_CLEANING_PREPARE_TIME_VALUE_Y 170
#define SETTINGS_CLEANING_PREPARE_TIME_VALUE_WIDTH 76
#define SETTINGS_CLEANING_PREPARE_TIME_VALUE_HEIGHT 36
#define SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_X 354
#define SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_Y 224
#define SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_WIDTH 62
#define SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_HEIGHT 32
#define SETTINGS_CLEANING_PREPARE_TIME_GROUP_X 0
#define SETTINGS_CLEANING_PREPARE_TIME_GROUP_Y 220
#define SETTINGS_CLEANING_PREPARE_TIME_GROUP_WIDTH SETTINGS_CLEANING_PREPARE_PANEL_WIDTH
#define SETTINGS_CLEANING_PREPARE_TIME_GROUP_HEIGHT 48
#define SETTINGS_CLEANING_PREPARE_TIME_ICON_AREA_WIDTH 44
#define SETTINGS_CLEANING_PREPARE_TIME_ICON_X 0
#define SETTINGS_CLEANING_PREPARE_TIME_ICON_Y 8
#define SETTINGS_CLEANING_PREPARE_TIME_ICON_SIZE 32
#define SETTINGS_CLEANING_PREPARE_TIME_TRACK_X SETTINGS_CLEANING_PREPARE_TIME_ICON_AREA_WIDTH
#define SETTINGS_CLEANING_PREPARE_TIME_TRACK_Y 19
#define SETTINGS_CLEANING_PREPARE_TIME_TRACK_WIDTH 304
#define SETTINGS_CLEANING_PREPARE_TIME_TRACK_HEIGHT 10
#define SETTINGS_CLEANING_PREPARE_TIME_TRACK_RADIUS 5
#define SETTINGS_CLEANING_PREPARE_TIME_KNOB_SIZE 30
#define SETTINGS_CLEANING_PREPARE_TIME_KNOB_Y 9
#define SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC 1
#define SETTINGS_CLEANING_PREPARE_TIME_DEFAULT_SEC 32
#define SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC 60
#define SETTINGS_CLEANING_PREPARE_TIME_PROGRESS_WIDTH \
    ((SETTINGS_CLEANING_PREPARE_TIME_TRACK_WIDTH * \
      (SETTINGS_CLEANING_PREPARE_TIME_DEFAULT_SEC - SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC)) / \
     (SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC - SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC))
#define SETTINGS_CLEANING_PREPARE_TIME_KNOB_X \
    (SETTINGS_CLEANING_PREPARE_TIME_TRACK_X + SETTINGS_CLEANING_PREPARE_TIME_PROGRESS_WIDTH - \
     (SETTINGS_CLEANING_PREPARE_TIME_KNOB_SIZE / 2))
#define SETTINGS_CLEANING_PREPARE_BUTTON_WIDTH 192
#define SETTINGS_CLEANING_PREPARE_BUTTON_HEIGHT 64
#define SETTINGS_CLEANING_PREPARE_CANCEL_X 0
#define SETTINGS_CLEANING_PREPARE_START_X 224
#define SETTINGS_CLEANING_PREPARE_BUTTON_Y 312
#define SETTINGS_CLEANING_PREPARE_BUTTON_RADIUS 32
#define SETTINGS_CLEANING_PREPARE_CANCEL_COLOR 0x3A3A3A

#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_NAME "Frame-5.png"
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_WIDTH 240
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_HEIGHT 240
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_X 56
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_Y 120
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_X 404
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_Y 160
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_WIDTH 312
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_HEIGHT 32
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_CANCEL_X 352
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_NEXT_X 576
#define SETTINGS_CLEANING_MAINTENANCE_PREPARE_BUTTON_Y 256

typedef enum {
    SETTINGS_CLEANING_RINSE_IDLE = 0,
    SETTINGS_CLEANING_RINSE_RUNNING,
    SETTINGS_CLEANING_RINSE_COMPLETE,
    SETTINGS_CLEANING_RINSE_INTERRUPTED,
} settings_cleaning_rinse_status_t;

typedef enum {
    SETTINGS_CLEANING_RINSE_AFTER_RETURN = 0,
    SETTINGS_CLEANING_RINSE_AFTER_SHOW_MAINTENANCE_WATER,
} settings_cleaning_rinse_after_action_t;

typedef enum {
    SETTINGS_CLEANING_MAINTENANCE_PREPARE_TABLET = 0,
    SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER,
} settings_cleaning_maintenance_prepare_step_t;

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
    bool starts_quick_rinse;
    bool opens_prepare;
    bool opens_maintenance_prepare;
    const char *maintenance_prepare_prompt;
    const char *maintenance_prepare_water_prompt;
    const char *maintenance_prepare_icon_name;
    settings_cleaning_rinse_after_action_t maintenance_prepare_after_action;
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
    lv_obj_t *prepare_overlay;
    lv_obj_t *prepare_time_group;
    lv_obj_t *prepare_time_progress_fill;
    lv_obj_t *prepare_time_knob;
    lv_obj_t *prepare_time_value_label;
    lv_timer_t *rinse_timer;
    lv_obj_t *rinse_overlay;
    lv_obj_t *rinse_button_label;
    lv_obj_t *rinse_helper_label;
    lv_obj_t *rinse_icon;
    int32_t descaling_level;
    int32_t prepare_time_sec;
    int32_t rinse_progress;
    uint32_t rinse_elapsed_ms;
    settings_cleaning_tab_t selected_tab;
    settings_cleaning_rinse_status_t rinse_status;
    settings_cleaning_rinse_after_action_t rinse_after_action;
    settings_cleaning_rinse_after_action_t maintenance_prepare_after_action;
    const char *maintenance_prepare_water_prompt;
    const char *maintenance_prepare_icon_name;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char icon_src[8][SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char rinse_status_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
} settings_cleaning_page_state_t;

static const settings_cleaning_menu_item_t settings_cleaning_menu_items[] = {
    {"日常清洗", SETTINGS_CLEANING_TAB_DAILY},
    {"机器维护清洁", SETTINGS_CLEANING_TAB_MAINTENANCE},
    {"除垢等级", SETTINGS_CLEANING_TAB_DESCALING_LEVEL},
};

static const settings_cleaning_action_item_t settings_cleaning_daily_items[] = {
    {"冲泡器简易清洗", "清洗", SETTINGS_CLEANING_CARD_ICON_NAME, true, false, false, NULL, NULL, NULL,
     SETTINGS_CLEANING_RINSE_AFTER_RETURN},
    {"奶泡器简易清洗", "清洗", SETTINGS_CLEANING_CARD_ICON_NAME, true, false, false, NULL, NULL, NULL,
     SETTINGS_CLEANING_RINSE_AFTER_RETURN},
    {"奶泡器深度清洗", "立即除垢", SETTINGS_CLEANING_CARD_ICON_NAME, false, true, false, NULL, NULL, NULL,
     SETTINGS_CLEANING_RINSE_AFTER_RETURN},
};

static const settings_cleaning_action_item_t settings_cleaning_maintenance_items[] = {
    {"冲泡器深度清洁（加药片）", "清洗", SETTINGS_CLEANING_CARD_ICON_NAME, false, false, true,
     "请向冲泡器中加入清水和药片", "请向奶罐加入清水", SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_NAME,
     SETTINGS_CLEANING_RINSE_AFTER_RETURN},
    {"奶泡器深度清洁（加药片）", "清洗", SETTINGS_CLEANING_CARD_ICON_NAME, false, false, true,
     "请向奶泡器中加入清水和药品", "请向奶罐加入清水", SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_NAME,
     SETTINGS_CLEANING_RINSE_AFTER_SHOW_MAINTENANCE_WATER},
    {"除垢", "立即除垢", SETTINGS_CLEANING_MAINTENANCE_DESCALING_ICON_NAME, false, false, true,
     "请向水箱中加入清水和清洁剂", "再向水箱加入清水", "Frame-6.png",
     SETTINGS_CLEANING_RINSE_AFTER_SHOW_MAINTENANCE_WATER},
};

static void settings_cleaning_delete_prepare_overlay(settings_cleaning_page_state_t *state);
static bool
settings_cleaning_create_daily_clean(settings_cleaning_page_state_t *state);
static bool
settings_cleaning_create_maintenance_clean(settings_cleaning_page_state_t *state);
static lv_obj_t *settings_cleaning_create_progress_segment(lv_obj_t *parent,
                                                           int32_t x,
                                                           int32_t y,
                                                           int32_t width,
                                                           int32_t height,
                                                           uint32_t color,
                                                           int32_t radius);

static void settings_cleaning_stop_rinse_timer(settings_cleaning_page_state_t *state)
{
    if (state == NULL || state->rinse_timer == NULL) {
        return;
    }

    lv_timer_del(state->rinse_timer);
    state->rinse_timer = NULL;
}

static void settings_cleaning_delete_rinse_overlay(settings_cleaning_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    settings_cleaning_stop_rinse_timer(state);
    if (state->rinse_overlay != NULL) {
        lv_obj_delete(state->rinse_overlay);
        state->rinse_overlay = NULL;
    }
    state->rinse_button_label = NULL;
    state->rinse_helper_label = NULL;
    state->rinse_icon = NULL;
    state->rinse_status = SETTINGS_CLEANING_RINSE_IDLE;
    state->rinse_after_action = SETTINGS_CLEANING_RINSE_AFTER_RETURN;
}

static void settings_cleaning_delete_prepare_overlay(settings_cleaning_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    if (state->prepare_overlay != NULL) {
        lv_obj_delete(state->prepare_overlay);
        state->prepare_overlay = NULL;
    }
    state->prepare_time_group = NULL;
    state->prepare_time_progress_fill = NULL;
    state->prepare_time_knob = NULL;
    state->prepare_time_value_label = NULL;
}

static void settings_cleaning_back_clicked(lv_event_t *event)
{
    lv_obj_t *screen;
    settings_cleaning_page_state_t *state;

    screen = lv_screen_active();
    state = screen == NULL ? NULL : (settings_cleaning_page_state_t *)lv_obj_get_user_data(screen);
    settings_cleaning_delete_prepare_overlay(state);
    settings_cleaning_delete_rinse_overlay(state);
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
    state->prepare_time_group = NULL;
    state->prepare_time_progress_fill = NULL;
    state->prepare_time_knob = NULL;
    state->prepare_time_value_label = NULL;
    state->rinse_button_label = NULL;
    state->rinse_helper_label = NULL;
    state->rinse_icon = NULL;
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

static bool settings_cleaning_create_action_button(lv_obj_t *parent, const char *text, lv_obj_t **created_button)
{
    lv_obj_t *button;

    if (created_button != NULL) {
        *created_button = NULL;
    }

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

    if (settings_cleaning_create_label(button,
                                       text,
                                       0,
                                       12,
                                       SETTINGS_CLEANING_ACTION_BUTTON_WIDTH,
                                       28,
                                       UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                       LV_TEXT_ALIGN_CENTER) == NULL) {
        return false;
    }

    if (created_button != NULL) {
        *created_button = button;
    }
    return true;
}

static void settings_cleaning_set_rinse_status(settings_cleaning_page_state_t *state,
                                               settings_cleaning_rinse_status_t status,
                                               int32_t progress);

static void
settings_cleaning_schedule_rinse_return(settings_cleaning_page_state_t *state);
static bool
settings_cleaning_create_maintenance_prepare_overlay(settings_cleaning_page_state_t *state,
                                                     settings_cleaning_maintenance_prepare_step_t step,
                                                     const char *tablet_prompt,
                                                     const char *water_prompt,
                                                     const char *icon_name,
                                                     settings_cleaning_rinse_after_action_t after_action);

static void settings_cleaning_set_rinse_final_layout(settings_cleaning_page_state_t *state, bool final_layout)
{
    if (state == NULL || state->rinse_button_label == NULL) {
        return;
    }

    if (final_layout) {
        lv_obj_set_x(state->rinse_button_label, SETTINGS_CLEANING_RINSE_BUTTON_LABEL_X);
        lv_obj_set_width(state->rinse_button_label, SETTINGS_CLEANING_RINSE_BUTTON_LABEL_WIDTH);
    } else {
        lv_obj_set_x(state->rinse_button_label, SETTINGS_CLEANING_RINSE_RUNNING_LABEL_X);
        lv_obj_set_width(state->rinse_button_label, SETTINGS_CLEANING_RINSE_RUNNING_LABEL_WIDTH);
        if (state->rinse_icon != NULL) {
            lv_obj_add_flag(state->rinse_icon, LV_OBJ_FLAG_HIDDEN);
        }
    }
}

static void settings_cleaning_set_rinse_status(settings_cleaning_page_state_t *state,
                                               settings_cleaning_rinse_status_t status,
                                               int32_t progress)
{
    const char *icon_name = NULL;

    if (state == NULL) {
        return;
    }

    if (progress < 0) {
        progress = 0;
    } else if (progress > 100) {
        progress = 100;
    }

    state->rinse_status = status;
    state->rinse_progress = progress;

    if (state->rinse_button_label != NULL) {
        switch (state->rinse_status) {
        case SETTINGS_CLEANING_RINSE_RUNNING:
            settings_cleaning_set_rinse_final_layout(state, false);
            lv_label_set_text_fmt(state->rinse_button_label, "清洗中 %d %%", state->rinse_progress);
            break;
        case SETTINGS_CLEANING_RINSE_COMPLETE:
            settings_cleaning_set_rinse_final_layout(state, true);
            lv_label_set_text(state->rinse_button_label, "清洗完成");
            icon_name = SETTINGS_CLEANING_RINSE_COMPLETE_ICON_NAME;
            break;
        case SETTINGS_CLEANING_RINSE_INTERRUPTED:
            settings_cleaning_set_rinse_final_layout(state, true);
            lv_label_set_text(state->rinse_button_label, "清洗中断");
            icon_name = SETTINGS_CLEANING_RINSE_INTERRUPTED_ICON_NAME;
            break;
        default:
            break;
        }
    }

    if (state->rinse_helper_label != NULL) {
        if (state->rinse_status == SETTINGS_CLEANING_RINSE_INTERRUPTED) {
            lv_obj_clear_flag(state->rinse_helper_label, LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(state->rinse_helper_label, LV_OBJ_FLAG_HIDDEN);
        }
    }

    if (state->rinse_icon != NULL) {
        if (icon_name != NULL &&
            ep_platform_lvgl_image_src(icon_name, state->rinse_status_src, sizeof(state->rinse_status_src)) == EP_OK) {
            lv_image_set_src(state->rinse_icon, state->rinse_status_src);
            lv_obj_clear_flag(state->rinse_icon, LV_OBJ_FLAG_HIDDEN);
        } else {
            lv_obj_add_flag(state->rinse_icon, LV_OBJ_FLAG_HIDDEN);
        }
    }

    if (state->rinse_status == SETTINGS_CLEANING_RINSE_COMPLETE ||
        state->rinse_status == SETTINGS_CLEANING_RINSE_INTERRUPTED) {
        settings_cleaning_schedule_rinse_return(state);
    }
}

static void settings_cleaning_rinse_return_timer_cb(lv_timer_t *timer)
{
    settings_cleaning_page_state_t *state;
    settings_cleaning_rinse_status_t completed_status;
    settings_cleaning_rinse_after_action_t after_action;

    state = (settings_cleaning_page_state_t *)lv_timer_get_user_data(timer);
    if (state == NULL) {
        return;
    }

    state->rinse_timer = NULL;
    completed_status = state->rinse_status;
    after_action = state->rinse_after_action;
    settings_cleaning_delete_rinse_overlay(state);

    if (completed_status == SETTINGS_CLEANING_RINSE_COMPLETE &&
        after_action == SETTINGS_CLEANING_RINSE_AFTER_SHOW_MAINTENANCE_WATER) {
        settings_cleaning_create_maintenance_prepare_overlay(
            state,
            SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER,
            NULL,
            state->maintenance_prepare_water_prompt,
            state->maintenance_prepare_icon_name,
            SETTINGS_CLEANING_RINSE_AFTER_RETURN);
    }
}

static void settings_cleaning_schedule_rinse_return(settings_cleaning_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    if (state->rinse_timer != NULL) {
        lv_timer_set_cb(state->rinse_timer, settings_cleaning_rinse_return_timer_cb);
        lv_timer_set_period(state->rinse_timer, SETTINGS_CLEANING_RINSE_RETURN_DELAY_MS);
        lv_timer_set_repeat_count(state->rinse_timer, 1);
        lv_timer_reset(state->rinse_timer);
        return;
    }

    state->rinse_timer = lv_timer_create(settings_cleaning_rinse_return_timer_cb,
                                         SETTINGS_CLEANING_RINSE_RETURN_DELAY_MS,
                                         state);
    if (state->rinse_timer != NULL) {
        lv_timer_set_repeat_count(state->rinse_timer, 1);
    }
}

static void settings_cleaning_rinse_timer_cb(lv_timer_t *timer)
{
    settings_cleaning_page_state_t *state;
    uint32_t progress;

    state = (settings_cleaning_page_state_t *)lv_timer_get_user_data(timer);
    if (state == NULL || state->rinse_status != SETTINGS_CLEANING_RINSE_RUNNING) {
        return;
    }

    state->rinse_elapsed_ms += SETTINGS_CLEANING_RINSE_TICK_MS;
    if (state->rinse_elapsed_ms >= SETTINGS_CLEANING_RINSE_DURATION_MS) {
        state->rinse_elapsed_ms = SETTINGS_CLEANING_RINSE_DURATION_MS;
        settings_cleaning_set_rinse_status(state, SETTINGS_CLEANING_RINSE_COMPLETE, 100);
        return;
    }

    progress = (state->rinse_elapsed_ms * 100u) / SETTINGS_CLEANING_RINSE_DURATION_MS;
    settings_cleaning_set_rinse_status(state, SETTINGS_CLEANING_RINSE_RUNNING, (int32_t)progress);
}

static bool settings_cleaning_load_icon(settings_cleaning_page_state_t *state,
                                        const char *icon_name,
                                        size_t image_index)
{
    return image_index < sizeof(state->icon_src) / sizeof(state->icon_src[0]) &&
           ep_platform_lvgl_image_src(icon_name, state->icon_src[image_index], sizeof(state->icon_src[image_index])) ==
               EP_OK;
}

static void settings_cleaning_rinse_status_clicked(lv_event_t *event);

static bool settings_cleaning_create_rinse_status_button(settings_cleaning_page_state_t *state)
{
    lv_obj_t *button;

    button = lv_button_create(state->rinse_overlay);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_CLEANING_RINSE_BUTTON_WIDTH, SETTINGS_CLEANING_RINSE_BUTTON_HEIGHT);
    lv_obj_set_pos(button, SETTINGS_CLEANING_RINSE_BUTTON_X, SETTINGS_CLEANING_RINSE_BUTTON_Y);
    lv_obj_set_style_bg_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_color(button, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_border_width(button, 1, LV_PART_MAIN);
    lv_obj_set_style_border_opa(button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(button, SETTINGS_CLEANING_RINSE_BUTTON_RADIUS, LV_PART_MAIN);
    lv_obj_clear_flag(button, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_event_cb(button, settings_cleaning_rinse_status_clicked, LV_EVENT_CLICKED, state);

    state->rinse_button_label = settings_cleaning_create_label(button,
                                                               "",
                                                               SETTINGS_CLEANING_RINSE_BUTTON_LABEL_X,
                                                               SETTINGS_CLEANING_RINSE_BUTTON_LABEL_Y,
                                                               SETTINGS_CLEANING_RINSE_BUTTON_LABEL_WIDTH,
                                                               SETTINGS_CLEANING_RINSE_BUTTON_LABEL_HEIGHT,
                                                               UI_STYLE_FONT_DETAILS_MODAL,
                                                               LV_TEXT_ALIGN_CENTER);
    if (state->rinse_button_label == NULL) {
        return false;
    }

    state->rinse_icon = lv_image_create(button);
    if (state->rinse_icon == NULL) {
        return false;
    }
    lv_obj_remove_style_all(state->rinse_icon);
    lv_obj_set_size(state->rinse_icon, SETTINGS_CLEANING_RINSE_STATUS_ICON_SIZE, SETTINGS_CLEANING_RINSE_STATUS_ICON_SIZE);
    lv_obj_set_pos(state->rinse_icon, SETTINGS_CLEANING_RINSE_STATUS_ICON_X, SETTINGS_CLEANING_RINSE_STATUS_ICON_Y);
    lv_obj_add_flag(state->rinse_icon, LV_OBJ_FLAG_HIDDEN);

    return true;
}

static bool settings_cleaning_create_rinse_status(settings_cleaning_page_state_t *state)
{
    if (state == NULL || state->screen == NULL) {
        return false;
    }

    settings_cleaning_delete_rinse_overlay(state);

    state->rinse_overlay = lv_obj_create(state->screen);
    if (state->rinse_overlay == NULL) {
        return false;
    }

    lv_obj_remove_style_all(state->rinse_overlay);
    lv_obj_set_size(state->rinse_overlay, SETTINGS_CLEANING_RINSE_PAGE_WIDTH, SETTINGS_CLEANING_RINSE_PAGE_HEIGHT);
    lv_obj_set_pos(state->rinse_overlay, 0, 0);
    lv_obj_set_style_bg_color(state->rinse_overlay, lv_color_hex(SETTINGS_PAGE_BG_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(state->rinse_overlay, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(state->rinse_overlay, LV_OBJ_FLAG_SCROLLABLE);

    if (!settings_cleaning_create_rinse_status_button(state)) {
        return false;
    }

    state->rinse_helper_label = settings_cleaning_create_label(state->rinse_overlay,
                                                               "请返回重试",
                                                               SETTINGS_CLEANING_RINSE_HELPER_X,
                                                               SETTINGS_CLEANING_RINSE_HELPER_Y,
                                                               SETTINGS_CLEANING_RINSE_HELPER_WIDTH,
                                                               SETTINGS_CLEANING_RINSE_HELPER_HEIGHT,
                                                               UI_STYLE_FONT_HOME_SIDE,
                                                               LV_TEXT_ALIGN_CENTER);
    if (state->rinse_helper_label == NULL) {
        return false;
    }
    lv_obj_add_flag(state->rinse_helper_label, LV_OBJ_FLAG_HIDDEN);

    state->rinse_elapsed_ms = 0u;
    settings_cleaning_set_rinse_status(state, SETTINGS_CLEANING_RINSE_RUNNING, 0);
    state->rinse_timer = lv_timer_create(settings_cleaning_rinse_timer_cb,
                                         SETTINGS_CLEANING_RINSE_TICK_MS,
                                         state);
    if (state->rinse_timer == NULL) {
        settings_cleaning_set_rinse_status(state, SETTINGS_CLEANING_RINSE_INTERRUPTED, state->rinse_progress);
        return false;
    }
    lv_timer_set_repeat_count(state->rinse_timer, -1);

    return true;
}

static void settings_cleaning_start_rinse(settings_cleaning_page_state_t *state,
                                          settings_cleaning_rinse_after_action_t after_action)
{
    if (state == NULL) {
        return;
    }

    state->rinse_status = SETTINGS_CLEANING_RINSE_IDLE;
    state->rinse_progress = 0;
    state->rinse_elapsed_ms = 0u;
    (void)settings_cleaning_create_rinse_status(state);
    state->rinse_after_action = after_action;
}

static void settings_cleaning_start_quick_rinse(settings_cleaning_page_state_t *state)
{
    settings_cleaning_start_rinse(state, SETTINGS_CLEANING_RINSE_AFTER_RETURN);
}

static void settings_cleaning_quick_rinse_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    settings_cleaning_start_quick_rinse(state);
}

static int32_t settings_cleaning_prepare_progress_width_for_time(int32_t time_sec)
{
    if (time_sec < SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC) {
        time_sec = SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC;
    } else if (time_sec > SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC) {
        time_sec = SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC;
    }

    return (SETTINGS_CLEANING_PREPARE_TIME_TRACK_WIDTH *
            (time_sec - SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC)) /
           (SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC - SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC);
}

static int32_t settings_cleaning_prepare_knob_x_for_time(int32_t time_sec)
{
    return SETTINGS_CLEANING_PREPARE_TIME_TRACK_X + settings_cleaning_prepare_progress_width_for_time(time_sec) -
           (SETTINGS_CLEANING_PREPARE_TIME_KNOB_SIZE / 2);
}

static int32_t settings_cleaning_prepare_time_for_point(settings_cleaning_page_state_t *state,
                                                        const lv_point_t *point)
{
    lv_area_t group_coords;
    int32_t relative_x;
    int32_t time_step;

    if (state == NULL || state->prepare_time_group == NULL || point == NULL) {
        return SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC;
    }

    lv_obj_get_coords(state->prepare_time_group, &group_coords);
    relative_x = point->x - group_coords.x1 - SETTINGS_CLEANING_PREPARE_TIME_TRACK_X;
    if (relative_x <= 0) {
        return SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC;
    }
    if (relative_x >= SETTINGS_CLEANING_PREPARE_TIME_TRACK_WIDTH) {
        return SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC;
    }

    time_step = (relative_x *
                     (SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC - SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC) +
                 (SETTINGS_CLEANING_PREPARE_TIME_TRACK_WIDTH / 2)) /
                SETTINGS_CLEANING_PREPARE_TIME_TRACK_WIDTH;
    return SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC + time_step;
}

static void settings_cleaning_set_prepare_time(settings_cleaning_page_state_t *state, int32_t time_sec)
{
    int32_t progress_width;

    if (state == NULL) {
        return;
    }

    if (time_sec < SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC) {
        time_sec = SETTINGS_CLEANING_PREPARE_TIME_MIN_SEC;
    } else if (time_sec > SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC) {
        time_sec = SETTINGS_CLEANING_PREPARE_TIME_MAX_SEC;
    }

    state->prepare_time_sec = time_sec;
    progress_width = settings_cleaning_prepare_progress_width_for_time(time_sec);

    if (state->prepare_time_progress_fill != NULL) {
        lv_obj_set_width(state->prepare_time_progress_fill, progress_width);
    }
    if (state->prepare_time_knob != NULL) {
        lv_obj_set_x(state->prepare_time_knob, settings_cleaning_prepare_knob_x_for_time(time_sec));
    }
    if (state->prepare_time_value_label != NULL) {
        lv_label_set_text_fmt(state->prepare_time_value_label, "%ds", state->prepare_time_sec);
    }
}

static void settings_cleaning_prepare_time_event(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;
    lv_point_t point;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL) {
        return;
    }

    lv_indev_get_point(lv_indev_active(), &point);
    settings_cleaning_set_prepare_time(state, settings_cleaning_prepare_time_for_point(state, &point));
}

static bool settings_cleaning_create_prepare_time_progress(settings_cleaning_page_state_t *state,
                                                           lv_obj_t *parent)
{
    lv_obj_t *group;
    lv_obj_t *image;
    lv_obj_t *track;
    lv_obj_t *knob;
    size_t image_index = 1u;

    group = lv_obj_create(parent);
    if (group == NULL) {
        return false;
    }

    lv_obj_remove_style_all(group);
    lv_obj_set_size(group, SETTINGS_CLEANING_PREPARE_TIME_GROUP_WIDTH, SETTINGS_CLEANING_PREPARE_TIME_GROUP_HEIGHT);
    lv_obj_set_pos(group, SETTINGS_CLEANING_PREPARE_TIME_GROUP_X, SETTINGS_CLEANING_PREPARE_TIME_GROUP_Y);
    lv_obj_set_style_bg_opa(group, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(group, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(group, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(group, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_flag(group, LV_OBJ_FLAG_CLICKABLE);
    lv_obj_add_event_cb(group, settings_cleaning_prepare_time_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(group, settings_cleaning_prepare_time_event, LV_EVENT_PRESSING, state);
    state->prepare_time_group = group;

    if (settings_cleaning_load_icon(state, SETTINGS_CLEANING_DESCALING_ICON_NAME, image_index)) {
        image = lv_image_create(group);
        if (image != NULL) {
            lv_obj_remove_style_all(image);
            lv_obj_set_size(image,
                            SETTINGS_CLEANING_PREPARE_TIME_ICON_SIZE,
                            SETTINGS_CLEANING_PREPARE_TIME_ICON_SIZE);
            lv_obj_set_pos(image, SETTINGS_CLEANING_PREPARE_TIME_ICON_X, SETTINGS_CLEANING_PREPARE_TIME_ICON_Y);
            lv_image_set_src(image, state->icon_src[image_index]);
        }
    }

    track = settings_cleaning_create_progress_segment(group,
                                                      SETTINGS_CLEANING_PREPARE_TIME_TRACK_X,
                                                      SETTINGS_CLEANING_PREPARE_TIME_TRACK_Y,
                                                      SETTINGS_CLEANING_PREPARE_TIME_TRACK_WIDTH,
                                                      SETTINGS_CLEANING_PREPARE_TIME_TRACK_HEIGHT,
                                                      SETTINGS_SHARED_GRAY_BORDER_COLOR,
                                                      SETTINGS_CLEANING_PREPARE_TIME_TRACK_RADIUS);
    if (track == NULL) {
        return false;
    }
    lv_obj_add_event_cb(track, settings_cleaning_prepare_time_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(track, settings_cleaning_prepare_time_event, LV_EVENT_PRESSING, state);

    state->prepare_time_progress_fill = settings_cleaning_create_progress_segment(
        track,
        0,
        0,
        SETTINGS_CLEANING_PREPARE_TIME_PROGRESS_WIDTH,
        SETTINGS_CLEANING_PREPARE_TIME_TRACK_HEIGHT,
        SETTINGS_CLEANING_LEVEL_GOLD_COLOR,
        SETTINGS_CLEANING_PREPARE_TIME_TRACK_RADIUS);
    if (state->prepare_time_progress_fill == NULL) {
        return false;
    }
    lv_obj_add_event_cb(state->prepare_time_progress_fill, settings_cleaning_prepare_time_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(state->prepare_time_progress_fill, settings_cleaning_prepare_time_event, LV_EVENT_PRESSING, state);

    knob = settings_cleaning_create_progress_segment(group,
                                                     SETTINGS_CLEANING_PREPARE_TIME_KNOB_X,
                                                     SETTINGS_CLEANING_PREPARE_TIME_KNOB_Y,
                                                     SETTINGS_CLEANING_PREPARE_TIME_KNOB_SIZE,
                                                     SETTINGS_CLEANING_PREPARE_TIME_KNOB_SIZE,
                                                     SETTINGS_PAGE_TEXT_COLOR,
                                                     SETTINGS_CLEANING_PREPARE_TIME_KNOB_SIZE / 2);
    if (knob == NULL) {
        return false;
    }
    state->prepare_time_knob = knob;
    lv_obj_add_event_cb(knob, settings_cleaning_prepare_time_event, LV_EVENT_PRESSED, state);
    lv_obj_add_event_cb(knob, settings_cleaning_prepare_time_event, LV_EVENT_PRESSING, state);

    settings_cleaning_set_prepare_time(state, state->prepare_time_sec);
    return true;
}

static bool settings_cleaning_create_prepare_button(lv_obj_t *parent,
                                                    const char *text,
                                                    int32_t x,
                                                    uint32_t color,
                                                    lv_event_cb_t clicked_cb,
                                                    settings_cleaning_page_state_t *state)
{
    lv_obj_t *button;

    button = lv_button_create(parent);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_CLEANING_PREPARE_BUTTON_WIDTH, SETTINGS_CLEANING_PREPARE_BUTTON_HEIGHT);
    lv_obj_set_pos(button, x, SETTINGS_CLEANING_PREPARE_BUTTON_Y);
    lv_obj_set_style_bg_color(button, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(button, SETTINGS_CLEANING_PREPARE_BUTTON_RADIUS, LV_PART_MAIN);
    lv_obj_clear_flag(button, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_event_cb(button, clicked_cb, LV_EVENT_CLICKED, state);

    return settings_cleaning_create_label(button,
                                          text,
                                          0,
                                          16,
                                          SETTINGS_CLEANING_PREPARE_BUTTON_WIDTH,
                                          32,
                                          UI_STYLE_FONT_HOME_SIDE,
                                          LV_TEXT_ALIGN_CENTER) != NULL;
}

static bool settings_cleaning_create_prepare_icon_box(settings_cleaning_page_state_t *state)
{
    lv_obj_t *box;
    lv_obj_t *image;
    size_t image_index = 0u;

    box = lv_obj_create(state->prepare_overlay);
    if (box == NULL) {
        return false;
    }

    lv_obj_remove_style_all(box);
    lv_obj_set_size(box, SETTINGS_CLEANING_PREPARE_ICON_BOX_WIDTH, SETTINGS_CLEANING_PREPARE_ICON_BOX_HEIGHT);
    lv_obj_set_pos(box, SETTINGS_CLEANING_PREPARE_ICON_BOX_X, SETTINGS_CLEANING_PREPARE_ICON_BOX_Y);
    lv_obj_set_style_bg_opa(box, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(box, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(box, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(box, LV_OBJ_FLAG_SCROLLABLE);

    if (!settings_cleaning_load_icon(state, SETTINGS_CLEANING_PREPARE_ICON_NAME, image_index)) {
        return true;
    }

    image = lv_image_create(box);
    if (image == NULL) {
        return false;
    }
    lv_obj_remove_style_all(image);
    lv_obj_set_size(image, SETTINGS_CLEANING_PREPARE_ICON_BOX_WIDTH, SETTINGS_CLEANING_PREPARE_ICON_BOX_HEIGHT);
    lv_obj_set_pos(image, 0, 0);
    lv_image_set_src(image, state->icon_src[image_index]);

    return true;
}

static void settings_cleaning_prepare_cancel_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    settings_cleaning_delete_prepare_overlay(state);
    (void)settings_cleaning_create_daily_clean(state);
}

static void settings_cleaning_prepare_start_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    settings_cleaning_delete_prepare_overlay(state);
    settings_cleaning_start_quick_rinse(state);
}

static bool settings_cleaning_create_prepare_overlay(settings_cleaning_page_state_t *state)
{
    lv_obj_t *panel;

    if (state == NULL || state->screen == NULL) {
        return false;
    }

    settings_cleaning_delete_prepare_overlay(state);
    settings_cleaning_delete_rinse_overlay(state);
    state->prepare_time_sec = SETTINGS_CLEANING_PREPARE_TIME_DEFAULT_SEC;

    state->prepare_overlay = lv_obj_create(state->screen);
    if (state->prepare_overlay == NULL) {
        return false;
    }

    lv_obj_remove_style_all(state->prepare_overlay);
    lv_obj_set_size(state->prepare_overlay, SETTINGS_CLEANING_PREPARE_PAGE_WIDTH, SETTINGS_CLEANING_PREPARE_PAGE_HEIGHT);
    lv_obj_set_pos(state->prepare_overlay, 0, 0);
    lv_obj_set_style_bg_color(state->prepare_overlay, lv_color_hex(SETTINGS_PAGE_BG_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(state->prepare_overlay, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(state->prepare_overlay, LV_OBJ_FLAG_SCROLLABLE);

    panel = lv_obj_create(state->prepare_overlay);
    if (panel == NULL) {
        return false;
    }
    lv_obj_remove_style_all(panel);
    lv_obj_set_size(panel, SETTINGS_CLEANING_PREPARE_PANEL_WIDTH, SETTINGS_CLEANING_PREPARE_PANEL_HEIGHT);
    lv_obj_set_pos(panel, SETTINGS_CLEANING_PREPARE_PANEL_X, SETTINGS_CLEANING_PREPARE_PANEL_Y);
    lv_obj_set_style_bg_opa(panel, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(panel, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(panel, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(panel, LV_OBJ_FLAG_SCROLLABLE);

    if (!settings_cleaning_create_prepare_icon_box(state) ||
        settings_cleaning_create_label(panel,
                                       "请向奶泡器中加入清水,\n并设置清洗时间",
                                       SETTINGS_CLEANING_PREPARE_PROMPT_X,
                                       SETTINGS_CLEANING_PREPARE_PROMPT_Y,
                                       SETTINGS_CLEANING_PREPARE_PROMPT_WIDTH,
                                       SETTINGS_CLEANING_PREPARE_PROMPT_HEIGHT,
                                       UI_STYLE_FONT_HOME_SIDE,
                                       LV_TEXT_ALIGN_CENTER) == NULL ||
        settings_cleaning_create_label(panel,
                                       "清洗时间",
                                       SETTINGS_CLEANING_PREPARE_TIME_LABEL_X,
                                       SETTINGS_CLEANING_PREPARE_TIME_LABEL_Y,
                                       SETTINGS_CLEANING_PREPARE_TIME_LABEL_WIDTH,
                                       SETTINGS_CLEANING_PREPARE_TIME_LABEL_HEIGHT,
                                       UI_STYLE_FONT_HOME_SIDE,
                                       LV_TEXT_ALIGN_LEFT) == NULL ||
        (state->prepare_time_value_label = settings_cleaning_create_label(
             panel,
             "32s",
             SETTINGS_CLEANING_PREPARE_TIME_VALUE_X,
             SETTINGS_CLEANING_PREPARE_TIME_VALUE_Y,
             SETTINGS_CLEANING_PREPARE_TIME_VALUE_WIDTH,
             SETTINGS_CLEANING_PREPARE_TIME_VALUE_HEIGHT,
             UI_STYLE_FONT_DETAILS_MODAL,
             LV_TEXT_ALIGN_CENTER)) == NULL ||
        settings_cleaning_create_gold_label(panel,
                                            "60s",
                                            SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_X,
                                            SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_Y,
                                            SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_WIDTH,
                                            SETTINGS_CLEANING_PREPARE_TIME_MAX_LABEL_HEIGHT,
                                            UI_STYLE_FONT_HOME_SIDE,
                                            LV_TEXT_ALIGN_CENTER) == NULL ||
        !settings_cleaning_create_prepare_time_progress(state, panel) ||
        !settings_cleaning_create_prepare_button(panel,
                                                 "取消",
                                                 SETTINGS_CLEANING_PREPARE_CANCEL_X,
                                                 SETTINGS_CLEANING_PREPARE_CANCEL_COLOR,
                                                 settings_cleaning_prepare_cancel_clicked,
                                                 state) ||
        !settings_cleaning_create_prepare_button(panel,
                                                 "开始清洗",
                                                 SETTINGS_CLEANING_PREPARE_START_X,
                                                 SETTINGS_CLEANING_ACTION_BUTTON_COLOR,
                                                 settings_cleaning_prepare_start_clicked,
                                                 state)) {
        return false;
    }

    return true;
}

static void settings_cleaning_prepare_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    (void)settings_cleaning_create_prepare_overlay(state);
}

static bool settings_cleaning_create_maintenance_prepare_icon_box(settings_cleaning_page_state_t *state)
{
    lv_obj_t *box;
    lv_obj_t *image;
    size_t image_index = 0u;

    box = lv_obj_create(state->prepare_overlay);
    if (box == NULL) {
        return false;
    }

    lv_obj_remove_style_all(box);
    lv_obj_set_size(box,
                    SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_WIDTH,
                    SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_HEIGHT);
    lv_obj_set_pos(box,
                   SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_X,
                   SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_Y);
    lv_obj_set_style_bg_opa(box, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(box, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(box, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(box, LV_OBJ_FLAG_SCROLLABLE);

    if (!settings_cleaning_load_icon(state, state->maintenance_prepare_icon_name, image_index)) {
        return true;
    }

    image = lv_image_create(box);
    if (image == NULL) {
        return false;
    }
    lv_obj_remove_style_all(image);
    lv_obj_set_size(image,
                    SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_WIDTH,
                    SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_BOX_HEIGHT);
    lv_obj_set_pos(image, 0, 0);
    lv_image_set_src(image, state->icon_src[image_index]);

    return true;
}

static bool settings_cleaning_create_maintenance_prepare_button(lv_obj_t *parent,
                                                                const char *text,
                                                                int32_t x,
                                                                uint32_t color,
                                                                lv_event_cb_t clicked_cb,
                                                                settings_cleaning_page_state_t *state)
{
    lv_obj_t *button;

    button = lv_button_create(parent);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_CLEANING_PREPARE_BUTTON_WIDTH, SETTINGS_CLEANING_PREPARE_BUTTON_HEIGHT);
    lv_obj_set_pos(button, x, SETTINGS_CLEANING_MAINTENANCE_PREPARE_BUTTON_Y);
    lv_obj_set_style_bg_color(button, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(button, SETTINGS_CLEANING_PREPARE_BUTTON_RADIUS, LV_PART_MAIN);
    lv_obj_clear_flag(button, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_add_event_cb(button, clicked_cb, LV_EVENT_CLICKED, state);

    return settings_cleaning_create_label(button,
                                          text,
                                          0,
                                          16,
                                          SETTINGS_CLEANING_PREPARE_BUTTON_WIDTH,
                                          32,
                                          UI_STYLE_FONT_HOME_SIDE,
                                          LV_TEXT_ALIGN_CENTER) != NULL;
}

static void settings_cleaning_maintenance_prepare_cancel_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    if (state != NULL && state->selected_tab == SETTINGS_CLEANING_TAB_MAINTENANCE) {
        settings_cleaning_delete_prepare_overlay(state);
        (void)settings_cleaning_create_maintenance_clean(state);
        return;
    }

    settings_cleaning_delete_prepare_overlay(state);
}

static void settings_cleaning_maintenance_prepare_next_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    settings_cleaning_delete_prepare_overlay(state);
    settings_cleaning_start_rinse(state, state->maintenance_prepare_after_action);
}

static void settings_cleaning_maintenance_prepare_clean_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    settings_cleaning_delete_prepare_overlay(state);
    settings_cleaning_start_rinse(state, SETTINGS_CLEANING_RINSE_AFTER_RETURN);
}

static bool settings_cleaning_create_maintenance_prepare_overlay(
    settings_cleaning_page_state_t *state,
    settings_cleaning_maintenance_prepare_step_t step,
    const char *tablet_prompt,
    const char *water_prompt,
    const char *icon_name,
    settings_cleaning_rinse_after_action_t after_action)
{
    const char *prompt;
    const char *next_text;
    lv_event_cb_t next_clicked_cb;

    if (state == NULL || state->screen == NULL) {
        return false;
    }

    state->maintenance_prepare_water_prompt = water_prompt == NULL ? "请向奶罐加入清水" : water_prompt;
    state->maintenance_prepare_icon_name = icon_name == NULL ? SETTINGS_CLEANING_MAINTENANCE_PREPARE_ICON_NAME :
                                                              icon_name;
    prompt = step == SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER ? state->maintenance_prepare_water_prompt :
                                                                   tablet_prompt;
    if (prompt == NULL) {
        prompt = "请向冲泡器中加入清水和药片";
    }
    next_text = step == SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER ? "清水" : "下一步";
    next_clicked_cb = step == SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER ?
                          settings_cleaning_maintenance_prepare_clean_clicked :
                          settings_cleaning_maintenance_prepare_next_clicked;
    state->maintenance_prepare_after_action = step == SETTINGS_CLEANING_MAINTENANCE_PREPARE_WATER ?
                                                  SETTINGS_CLEANING_RINSE_AFTER_RETURN :
                                                  after_action;

    settings_cleaning_delete_prepare_overlay(state);
    settings_cleaning_delete_rinse_overlay(state);

    state->prepare_overlay = lv_obj_create(state->screen);
    if (state->prepare_overlay == NULL) {
        return false;
    }

    lv_obj_remove_style_all(state->prepare_overlay);
    lv_obj_set_size(state->prepare_overlay, SETTINGS_CLEANING_PREPARE_PAGE_WIDTH, SETTINGS_CLEANING_PREPARE_PAGE_HEIGHT);
    lv_obj_set_pos(state->prepare_overlay, 0, 0);
    lv_obj_set_style_bg_color(state->prepare_overlay, lv_color_hex(SETTINGS_PAGE_BG_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(state->prepare_overlay, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(state->prepare_overlay, LV_OBJ_FLAG_SCROLLABLE);

    if (!settings_cleaning_create_maintenance_prepare_icon_box(state) ||
        settings_cleaning_create_label(state->prepare_overlay,
                                       prompt,
                                       SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_X,
                                       SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_Y,
                                       SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_WIDTH,
                                       SETTINGS_CLEANING_MAINTENANCE_PREPARE_PROMPT_HEIGHT,
                                       UI_STYLE_FONT_HOME_SIDE,
                                       LV_TEXT_ALIGN_CENTER) == NULL ||
        !settings_cleaning_create_maintenance_prepare_button(
            state->prepare_overlay,
            "取消",
            SETTINGS_CLEANING_MAINTENANCE_PREPARE_CANCEL_X,
            SETTINGS_CLEANING_PREPARE_CANCEL_COLOR,
            settings_cleaning_maintenance_prepare_cancel_clicked,
            state) ||
        !settings_cleaning_create_maintenance_prepare_button(
            state->prepare_overlay,
            next_text,
            SETTINGS_CLEANING_MAINTENANCE_PREPARE_NEXT_X,
            SETTINGS_CLEANING_ACTION_BUTTON_COLOR,
            next_clicked_cb,
            state)) {
        return false;
    }

    return true;
}

static void settings_cleaning_maintenance_prepare_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;
    const settings_cleaning_action_item_t *item;

    item = (const settings_cleaning_action_item_t *)lv_event_get_user_data(event);
    state = (settings_cleaning_page_state_t *)(lv_screen_active() == NULL ? NULL :
                                               lv_obj_get_user_data(lv_screen_active()));
    (void)settings_cleaning_create_maintenance_prepare_overlay(
        state,
        SETTINGS_CLEANING_MAINTENANCE_PREPARE_TABLET,
        item == NULL ? NULL : item->maintenance_prepare_prompt,
        item == NULL ? NULL : item->maintenance_prepare_water_prompt,
        item == NULL ? NULL : item->maintenance_prepare_icon_name,
        item == NULL ? SETTINGS_CLEANING_RINSE_AFTER_RETURN : item->maintenance_prepare_after_action);
}

static bool settings_cleaning_create_clean_card(settings_cleaning_page_state_t *state,
                                                const settings_cleaning_action_item_t *item,
                                                size_t index)
{
    lv_obj_t *card;
    lv_obj_t *button;
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
    if (item->starts_quick_rinse) {
        lv_obj_add_flag(card, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(card, settings_cleaning_quick_rinse_clicked, LV_EVENT_CLICKED, state);
    } else if (item->opens_prepare) {
        lv_obj_add_flag(card, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(card, settings_cleaning_prepare_clicked, LV_EVENT_CLICKED, state);
    } else if (item->opens_maintenance_prepare) {
        lv_obj_add_flag(card, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(card, settings_cleaning_maintenance_prepare_clicked, LV_EVENT_CLICKED, (void *)item);
    }

    if (settings_cleaning_load_icon(state, item->icon_name, index)) {
        image = lv_image_create(card);
        if (image != NULL) {
            lv_obj_remove_style_all(image);
            lv_obj_set_size(image, SETTINGS_CLEANING_CARD_ICON_SIZE, SETTINGS_CLEANING_CARD_ICON_SIZE);
            lv_obj_set_pos(image, SETTINGS_CLEANING_CARD_ICON_X, SETTINGS_CLEANING_CARD_ICON_Y);
            lv_image_set_src(image, state->icon_src[index]);
        }
    }

    if (settings_cleaning_create_label(card,
                                       item->title,
                                       SETTINGS_CLEANING_CARD_TEXT_X,
                                       SETTINGS_CLEANING_CARD_TEXT_Y,
                                       SETTINGS_CLEANING_CARD_TEXT_WIDTH,
                                       SETTINGS_CLEANING_CARD_TEXT_HEIGHT,
                                       UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                       LV_TEXT_ALIGN_LEFT) == NULL) {
        return false;
    }

    if (!settings_cleaning_create_action_button(card, item->button_text, &button)) {
        return false;
    }

    if (item->starts_quick_rinse) {
        lv_obj_add_event_cb(button, settings_cleaning_quick_rinse_clicked, LV_EVENT_CLICKED, state);
    } else if (item->opens_prepare) {
        lv_obj_add_event_cb(button, settings_cleaning_prepare_clicked, LV_EVENT_CLICKED, state);
    } else if (item->opens_maintenance_prepare) {
        lv_obj_add_event_cb(button, settings_cleaning_maintenance_prepare_clicked, LV_EVENT_CLICKED, (void *)item);
    }

    return true;
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

static void settings_cleaning_rinse_status_clicked(lv_event_t *event)
{
    settings_cleaning_page_state_t *state;

    state = (settings_cleaning_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL) {
        return;
    }

    if (state->rinse_status == SETTINGS_CLEANING_RINSE_RUNNING) {
        settings_cleaning_set_rinse_status(state, SETTINGS_CLEANING_RINSE_INTERRUPTED, state->rinse_progress);
        return;
    }

    state->rinse_status = SETTINGS_CLEANING_RINSE_IDLE;
    state->rinse_progress = 0;
    state->rinse_elapsed_ms = 0u;
    settings_cleaning_delete_rinse_overlay(state);
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
            settings_cleaning_delete_prepare_overlay(state);
            settings_cleaning_delete_rinse_overlay(state);
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
    settings_cleaning_delete_prepare_overlay(state);
    settings_cleaning_delete_rinse_overlay(state);
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
    state->prepare_time_sec = SETTINGS_CLEANING_PREPARE_TIME_DEFAULT_SEC;
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
