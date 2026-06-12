#include "pages/settings_page.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "lvgl.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>

#define SETTINGS_DETAILS_TITLE_TEXT "详细信息"
#define SETTINGS_DETAILS_HEADER_HEIGHT 96
#define SETTINGS_DETAILS_TITLE_X 344
#define SETTINGS_DETAILS_TITLE_Y 36
#define SETTINGS_DETAILS_TITLE_WIDTH 112
#define SETTINGS_DETAILS_TITLE_HEIGHT 48

#define SETTINGS_DETAILS_MENU_WIDTH 240
#define SETTINGS_DETAILS_MENU_Y SETTINGS_DETAILS_HEADER_HEIGHT
#define SETTINGS_DETAILS_MENU_HEIGHT (SETTINGS_PAGE_SCREEN_HEIGHT - SETTINGS_DETAILS_MENU_Y)
#define SETTINGS_DETAILS_MENU_ITEM_COUNT 3u
#define SETTINGS_DETAILS_MENU_ROW_HEIGHT 101
#define SETTINGS_DETAILS_MENU_SELECTED_COLOR 0x000000
#define SETTINGS_DETAILS_MENU_UNSELECTED_COLOR SETTINGS_PAGE_BUTTON_COLOR
#define SETTINGS_DETAILS_MENU_SEPARATOR_COLOR 0x3A3A3A
#define SETTINGS_DETAILS_MENU_LABEL_X 32
#define SETTINGS_DETAILS_MENU_LABEL_Y 28
#define SETTINGS_DETAILS_MENU_VALUE_Y 66
#define SETTINGS_DETAILS_MENU_LABEL_WIDTH 176
#define SETTINGS_DETAILS_MENU_LABEL_HEIGHT 32

#define SETTINGS_DETAILS_CONTENT_X SETTINGS_DETAILS_MENU_WIDTH
#define SETTINGS_DETAILS_CONTENT_Y SETTINGS_DETAILS_HEADER_HEIGHT
#define SETTINGS_DETAILS_CONTENT_WIDTH 560
#define SETTINGS_DETAILS_CONTENT_HEIGHT 404
#define SETTINGS_DETAILS_CONTENT_PAD_X 28
#define SETTINGS_DETAILS_CONTENT_PAD_TOP 16

#define SETTINGS_DETAILS_DRINK_CARD_WIDTH 236
#define SETTINGS_DETAILS_DRINK_CARD_HEIGHT 96
#define SETTINGS_DETAILS_DRINK_CARD_GAP_X 24
#define SETTINGS_DETAILS_DRINK_CARD_GAP_Y 24
#define SETTINGS_DETAILS_DRINK_CARD_RADIUS 12
#define SETTINGS_DETAILS_DRINK_IMAGE_SIZE 64
#define SETTINGS_DETAILS_DRINK_IMAGE_NATIVE_SIZE 240
#define SETTINGS_DETAILS_DRINK_IMAGE_SCALE ((SETTINGS_DETAILS_DRINK_IMAGE_SIZE * 256) / SETTINGS_DETAILS_DRINK_IMAGE_NATIVE_SIZE)
#define SETTINGS_DETAILS_DRINK_IMAGE_X 32
#define SETTINGS_DETAILS_DRINK_IMAGE_Y 16
#define SETTINGS_DETAILS_DRINK_TEXT_X 120
#define SETTINGS_DETAILS_DRINK_NAME_Y 24
#define SETTINGS_DETAILS_DRINK_COUNT_Y 60

#define SETTINGS_DETAILS_INFO_CARD_X 28
#define SETTINGS_DETAILS_INFO_CARD_Y 28
#define SETTINGS_DETAILS_INFO_CARD_WIDTH 496
#define SETTINGS_DETAILS_INFO_CARD_HEIGHT 215
#define SETTINGS_DETAILS_INFO_CARD_RADIUS 16
#define SETTINGS_DETAILS_DESCALING_ICON_NAME "settings_details_descaling_icon.png"
#define SETTINGS_DETAILS_DESCALING_ICON_SIZE 64
#define SETTINGS_DETAILS_DESCALING_ICON_X 32
#define SETTINGS_DETAILS_DESCALING_ICON_Y 16
#define SETTINGS_DETAILS_DESCALING_CARD_HEIGHT 96
#define SETTINGS_DETAILS_DESCALING_CARD_RADIUS 16

#define SETTINGS_DETAILS_MACHINE_ROW_HEIGHT 36
#define SETTINGS_DETAILS_MACHINE_LABEL_X 16
#define SETTINGS_DETAILS_MACHINE_VALUE_X 248
#define SETTINGS_DETAILS_MACHINE_FIRST_Y 16
#define SETTINGS_DETAILS_MACHINE_LABEL_WIDTH 224
#define SETTINGS_DETAILS_MACHINE_VALUE_WIDTH 232

#define SETTINGS_DETAILS_FACTORY_BUTTON_WIDTH 240
#define SETTINGS_DETAILS_FACTORY_BUTTON_HEIGHT 64
#define SETTINGS_DETAILS_FACTORY_BUTTON_X 160
#define SETTINGS_DETAILS_FACTORY_BUTTON_Y 268
#define SETTINGS_DETAILS_FACTORY_BUTTON_RADIUS 32

#define SETTINGS_DETAILS_MODAL_TEXT_X 275
#define SETTINGS_DETAILS_MODAL_TEXT_Y 155
#define SETTINGS_DETAILS_MODAL_TEXT_WIDTH 250
#define SETTINGS_DETAILS_MODAL_TEXT_HEIGHT 42
#define SETTINGS_DETAILS_MODAL_BUTTON_WIDTH 240
#define SETTINGS_DETAILS_MODAL_BUTTON_HEIGHT 64
#define SETTINGS_DETAILS_MODAL_BUTTON_Y 252
#define SETTINGS_DETAILS_MODAL_CANCEL_X 131
#define SETTINGS_DETAILS_MODAL_CONFIRM_X 429
#define SETTINGS_DETAILS_MODAL_BUTTON_RADIUS 32
#define SETTINGS_DETAILS_MODAL_CANCEL_COLOR SETTINGS_PAGE_BUTTON_COLOR
#define SETTINGS_DETAILS_MODAL_CONFIRM_COLOR 0xB56A2E

typedef enum {
    SETTINGS_DETAILS_TAB_DRINKS = 0,
    SETTINGS_DETAILS_TAB_DESCALING,
    SETTINGS_DETAILS_TAB_MACHINE,
} settings_details_tab_t;

typedef struct {
    const char *title;
    const char *value;
    settings_details_tab_t tab;
} settings_details_menu_item_t;

typedef struct {
    const char *name;
    const char *count;
    const char *image_name;
} settings_details_drink_t;

typedef struct {
    const char *label;
    const char *value;
} settings_details_machine_info_t;

typedef struct {
    lv_obj_t *screen;
    lv_obj_t *content;
    lv_obj_t *menu_rows[SETTINGS_DETAILS_MENU_ITEM_COUNT];
    lv_obj_t *menu_titles[SETTINGS_DETAILS_MENU_ITEM_COUNT];
    lv_obj_t *menu_values[SETTINGS_DETAILS_MENU_ITEM_COUNT];
    lv_obj_t *factory_modal;
    settings_details_tab_t selected_tab;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char image_src[12][SETTINGS_PAGE_SRC_BUFFER_SIZE];
} settings_details_page_state_t;

static const settings_details_menu_item_t settings_details_menu_items[] = {
    {"饮品杯数统计", "234344", SETTINGS_DETAILS_TAB_DRINKS},
    {"除垢次数", "123", SETTINGS_DETAILS_TAB_DESCALING},
    {"机器信息", "CM01", SETTINGS_DETAILS_TAB_MACHINE},
};

static const settings_details_drink_t settings_details_drinks[] = {
    {"意式浓缩", "12344", "0e6562f2-2397-4905-9d4d-7090309e36a7.png"},
    {"意式大杯", "12344", "6e1f8f76-6bbe-4dbf-8715-a8787158f4eb.png"},
    {"美式咖啡", "12344", "6d1012ac-0238-4f72-9315-10e2c1d6cd47.png"},
    {"卡布奇诺", "12344", "4ef84153-486b-4785-97f5-a70ab6c5b694.png"},
    {"拿铁咖啡", "12344", "9faccf31-9a18-4278-9191-014519634638.png"},
    {"拿铁玛琪雅朵", "12344", "56f5111c-f133-4a84-a9f3-1d2f8db03c5e.png"},
    {"热牛奶", "12344", "60ff2cef-b3b1-4fba-989b-aefc398dd29e.png"},
    {"热水", "12344", "6f111efb-d37b-4505-9fe2-c6425a691303.png"},
};

static const settings_details_machine_info_t settings_details_machine_infos[] = {
    {"型号:", "CM01"},
    {"HMI版本号:", "V1.0.0"},
    {"OS版本号:", "V1.0.0"},
    {"CTR版本号:", "V1.0.1"},
    {"SN号:", "HSUIDF29023209023"},
};

static void settings_details_show_factory_modal(settings_details_page_state_t *state, bool visible);

static void settings_details_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static void settings_details_clear_content(settings_details_page_state_t *state)
{
    if (state == NULL || state->content == NULL) {
        return;
    }

    lv_obj_clean(state->content);
    lv_obj_clear_flag(state->content, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_scrollbar_mode(state->content, LV_SCROLLBAR_MODE_OFF);
}

static void settings_details_refresh_menu(settings_details_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    for (size_t i = 0u; i < SETTINGS_DETAILS_MENU_ITEM_COUNT; ++i) {
        bool selected = settings_details_menu_items[i].tab == state->selected_tab;
        lv_color_t text_color = lv_color_white();

        if (state->menu_rows[i] != NULL) {
            lv_obj_set_style_bg_color(
                state->menu_rows[i],
                lv_color_hex(selected ? SETTINGS_DETAILS_MENU_SELECTED_COLOR : SETTINGS_DETAILS_MENU_UNSELECTED_COLOR),
                LV_PART_MAIN);
            lv_obj_set_style_bg_opa(state->menu_rows[i], LV_OPA_COVER, LV_PART_MAIN);
        }

        if (state->menu_titles[i] != NULL) {
            lv_obj_set_style_text_color(state->menu_titles[i], text_color, LV_PART_MAIN);
        }

        if (state->menu_values[i] != NULL) {
            lv_obj_set_style_text_color(state->menu_values[i], text_color, LV_PART_MAIN);
        }
    }

}

static lv_obj_t *settings_details_create_label(lv_obj_t *parent,
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

static bool settings_details_create_title(settings_details_page_state_t *state)
{
    return settings_details_create_label(state->screen,
                                         SETTINGS_DETAILS_TITLE_TEXT,
                                         SETTINGS_DETAILS_TITLE_X,
                                         SETTINGS_DETAILS_TITLE_Y,
                                         SETTINGS_DETAILS_TITLE_WIDTH,
                                         SETTINGS_DETAILS_TITLE_HEIGHT,
                                         UI_STYLE_FONT_HOME_USER,
                                         LV_TEXT_ALIGN_CENTER) != NULL;
}

static bool settings_details_load_recipe_image(const char *image_name,
                                               char *src,
                                               size_t src_size)
{
    return ep_platform_lvgl_recipe_src(image_name, src, src_size) == EP_OK;
}

static bool settings_details_create_drink_card(settings_details_page_state_t *state,
                                               const settings_details_drink_t *drink,
                                               size_t index)
{
    lv_obj_t *card;
    lv_obj_t *image;
    int32_t col;
    int32_t row;
    int32_t x;
    int32_t y;

    col = (int32_t)(index % 2u);
    row = (int32_t)(index / 2u);
    x = SETTINGS_DETAILS_CONTENT_PAD_X +
        col * (SETTINGS_DETAILS_DRINK_CARD_WIDTH + SETTINGS_DETAILS_DRINK_CARD_GAP_X);
    y = SETTINGS_DETAILS_CONTENT_PAD_TOP +
        row * (SETTINGS_DETAILS_DRINK_CARD_HEIGHT + SETTINGS_DETAILS_DRINK_CARD_GAP_Y);

    card = lv_obj_create(state->content);
    if (card == NULL) {
        return false;
    }

    lv_obj_remove_style_all(card);
    lv_obj_set_size(card, SETTINGS_DETAILS_DRINK_CARD_WIDTH, SETTINGS_DETAILS_DRINK_CARD_HEIGHT);
    lv_obj_set_pos(card, x, y);
    lv_obj_set_style_bg_color(card, lv_color_hex(SETTINGS_PAGE_BUTTON_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(card, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(card, SETTINGS_DETAILS_DRINK_CARD_RADIUS, LV_PART_MAIN);
    lv_obj_clear_flag(card, LV_OBJ_FLAG_SCROLLABLE);

    if (index < sizeof(state->image_src) / sizeof(state->image_src[0]) &&
        settings_details_load_recipe_image(drink->image_name, state->image_src[index], sizeof(state->image_src[index]))) {
        image = lv_image_create(card);
        if (image != NULL) {
            lv_obj_remove_style_all(image);
            lv_obj_set_pos(image, SETTINGS_DETAILS_DRINK_IMAGE_X, SETTINGS_DETAILS_DRINK_IMAGE_Y);
            lv_image_set_src(image, state->image_src[index]);
            lv_image_set_pivot(image, 0, 0);
            lv_image_set_scale(image, SETTINGS_DETAILS_DRINK_IMAGE_SCALE);
        }
    }

    if (settings_details_create_label(card,
                                      drink->name,
                                      SETTINGS_DETAILS_DRINK_TEXT_X,
                                      SETTINGS_DETAILS_DRINK_NAME_Y,
                                      96,
                                      32,
                                      UI_STYLE_FONT_DETAILS_DRINK,
                                      LV_TEXT_ALIGN_LEFT) == NULL ||
        settings_details_create_label(card,
                                      drink->count,
                                      SETTINGS_DETAILS_DRINK_TEXT_X,
                                      SETTINGS_DETAILS_DRINK_COUNT_Y,
                                      96,
                                      28,
                                      UI_STYLE_FONT_HOME_SIDE,
                                      LV_TEXT_ALIGN_LEFT) == NULL) {
        return false;
    }

    return true;
}

static bool settings_details_create_drink_statistics(settings_details_page_state_t *state)
{
    settings_details_clear_content(state);
    lv_obj_add_flag(state->content, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_scroll_dir(state->content, LV_DIR_VER);
    lv_obj_set_scrollbar_mode(state->content, LV_SCROLLBAR_MODE_AUTO);

    for (size_t i = 0u; i < sizeof(settings_details_drinks) / sizeof(settings_details_drinks[0]); ++i) {
        if (!settings_details_create_drink_card(state, &settings_details_drinks[i], i)) {
            return false;
        }
    }

    return true;
}

static bool settings_details_create_info_card(settings_details_page_state_t *state, lv_obj_t **card_out)
{
    lv_obj_t *card;

    card = lv_obj_create(state->content);
    if (card == NULL) {
        return false;
    }

    lv_obj_remove_style_all(card);
    lv_obj_set_size(card, SETTINGS_DETAILS_INFO_CARD_WIDTH, SETTINGS_DETAILS_INFO_CARD_HEIGHT);
    lv_obj_set_pos(card, SETTINGS_DETAILS_INFO_CARD_X, SETTINGS_DETAILS_INFO_CARD_Y);
    lv_obj_set_style_bg_color(card, lv_color_hex(SETTINGS_PAGE_BUTTON_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(card, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(card, SETTINGS_DETAILS_INFO_CARD_RADIUS, LV_PART_MAIN);
    lv_obj_clear_flag(card, LV_OBJ_FLAG_SCROLLABLE);
    *card_out = card;

    return true;
}

static bool settings_details_create_descaling(settings_details_page_state_t *state)
{
    lv_obj_t *card;
    lv_obj_t *image;
    size_t image_index = 0u;

    settings_details_clear_content(state);
    if (!settings_details_create_info_card(state, &card)) {
        return false;
    }
    lv_obj_set_size(card, SETTINGS_DETAILS_INFO_CARD_WIDTH, SETTINGS_DETAILS_DESCALING_CARD_HEIGHT);
    lv_obj_set_style_radius(card, SETTINGS_DETAILS_DESCALING_CARD_RADIUS, LV_PART_MAIN);

    if (ep_platform_lvgl_image_src(SETTINGS_DETAILS_DESCALING_ICON_NAME,
                                   state->image_src[image_index],
                                   sizeof(state->image_src[image_index])) == EP_OK) {
        image = lv_image_create(card);
        if (image != NULL) {
            lv_obj_remove_style_all(image);
            lv_obj_set_size(image, SETTINGS_DETAILS_DESCALING_ICON_SIZE, SETTINGS_DETAILS_DESCALING_ICON_SIZE);
            lv_obj_set_pos(image, SETTINGS_DETAILS_DESCALING_ICON_X, SETTINGS_DETAILS_DESCALING_ICON_Y);
            lv_image_set_src(image, state->image_src[image_index]);
        }
    }

    return settings_details_create_label(card,
                                         "除垢次数",
                                         144,
                                         24,
                                         180,
                                         32,
                                         UI_STYLE_FONT_DETAILS_MENU_VALUE,
                                         LV_TEXT_ALIGN_LEFT) != NULL &&
           settings_details_create_label(card,
                                         "12344",
                                         144,
                                         60,
                                         120,
                                         28,
                                         UI_STYLE_FONT_DETAILS_MENU_VALUE,
                                         LV_TEXT_ALIGN_LEFT) != NULL;
}

static void settings_details_factory_button_clicked(lv_event_t *event);

static bool settings_details_create_machine_info(settings_details_page_state_t *state)
{
    lv_obj_t *card;
    lv_obj_t *button;
    size_t count;

    settings_details_clear_content(state);
    if (!settings_details_create_info_card(state, &card)) {
        return false;
    }

    count = sizeof(settings_details_machine_infos) / sizeof(settings_details_machine_infos[0]);
    for (size_t i = 0u; i < count; ++i) {
        int32_t y = SETTINGS_DETAILS_MACHINE_FIRST_Y + (int32_t)i * SETTINGS_DETAILS_MACHINE_ROW_HEIGHT;

        if (settings_details_create_label(card,
                                          settings_details_machine_infos[i].label,
                                          SETTINGS_DETAILS_MACHINE_LABEL_X,
                                          y,
                                          SETTINGS_DETAILS_MACHINE_LABEL_WIDTH,
                                          32,
                                          UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                          LV_TEXT_ALIGN_LEFT) == NULL ||
            settings_details_create_label(card,
                                          settings_details_machine_infos[i].value,
                                          SETTINGS_DETAILS_MACHINE_VALUE_X,
                                          y,
                                          SETTINGS_DETAILS_MACHINE_VALUE_WIDTH,
                                          32,
                                          UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                          LV_TEXT_ALIGN_RIGHT) == NULL) {
            return false;
        }
    }

    button = lv_button_create(state->content);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_DETAILS_FACTORY_BUTTON_WIDTH, SETTINGS_DETAILS_FACTORY_BUTTON_HEIGHT);
    lv_obj_set_pos(button, SETTINGS_DETAILS_FACTORY_BUTTON_X, SETTINGS_DETAILS_FACTORY_BUTTON_Y);
    lv_obj_set_style_bg_color(button, lv_color_hex(SETTINGS_PAGE_BUTTON_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(button, SETTINGS_DETAILS_FACTORY_BUTTON_RADIUS, LV_PART_MAIN);
    lv_obj_add_event_cb(button, settings_details_factory_button_clicked, LV_EVENT_CLICKED, state);

    return settings_details_create_label(button,
                                         "恢复出厂设置",
                                         48,
                                         16,
                                         144,
                                         32,
                                         UI_STYLE_FONT_HOME_SIDE,
                                         LV_TEXT_ALIGN_CENTER) != NULL;
}

static bool settings_details_create_content_for_tab(settings_details_page_state_t *state)
{
    switch (state->selected_tab) {
    case SETTINGS_DETAILS_TAB_DRINKS:
        return settings_details_create_drink_statistics(state);
    case SETTINGS_DETAILS_TAB_DESCALING:
        return settings_details_create_descaling(state);
    case SETTINGS_DETAILS_TAB_MACHINE:
        return settings_details_create_machine_info(state);
    default:
        return false;
    }
}

static void settings_details_menu_row_clicked(lv_event_t *event)
{
    settings_details_page_state_t *state;
    lv_obj_t *target;

    state = (settings_details_page_state_t *)lv_event_get_user_data(event);
    target = lv_event_get_current_target_obj(event);
    if (state == NULL || target == NULL) {
        return;
    }

    for (size_t i = 0u; i < SETTINGS_DETAILS_MENU_ITEM_COUNT; ++i) {
        if (state->menu_rows[i] == target ||
            state->menu_titles[i] == target ||
            state->menu_values[i] == target) {
            state->selected_tab = settings_details_menu_items[i].tab;
            settings_details_refresh_menu(state);
            (void)settings_details_create_content_for_tab(state);
            return;
        }
    }
}

static bool settings_details_create_menu(settings_details_page_state_t *state)
{
    lv_obj_t *menu;

    menu = lv_obj_create(state->screen);
    if (menu == NULL) {
        return false;
    }

    lv_obj_remove_style_all(menu);
    lv_obj_set_size(menu, SETTINGS_DETAILS_MENU_WIDTH, SETTINGS_DETAILS_MENU_HEIGHT);
    lv_obj_set_pos(menu, 0, SETTINGS_DETAILS_MENU_Y);
    lv_obj_set_style_bg_color(menu, lv_color_hex(SETTINGS_PAGE_BUTTON_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(menu, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(menu, LV_OBJ_FLAG_SCROLLABLE);

    for (size_t i = 0u; i < SETTINGS_DETAILS_MENU_ITEM_COUNT; ++i) {
        lv_obj_t *row;
        int32_t y = (int32_t)i * SETTINGS_DETAILS_MENU_ROW_HEIGHT;

        row = lv_obj_create(menu);
        if (row == NULL) {
            return false;
        }

        state->menu_rows[i] = row;
        lv_obj_remove_style_all(row);
        lv_obj_set_size(row, SETTINGS_DETAILS_MENU_WIDTH, SETTINGS_DETAILS_MENU_ROW_HEIGHT);
        lv_obj_set_pos(row, 0, y);
        lv_obj_set_style_border_color(row, lv_color_hex(SETTINGS_DETAILS_MENU_SEPARATOR_COLOR), LV_PART_MAIN);
        lv_obj_set_style_border_width(row, i + 1u == SETTINGS_DETAILS_MENU_ITEM_COUNT ? 0 : 1, LV_PART_MAIN);
        lv_obj_set_style_border_side(row, LV_BORDER_SIDE_BOTTOM, LV_PART_MAIN);
        lv_obj_clear_flag(row, LV_OBJ_FLAG_SCROLLABLE);
        lv_obj_add_flag(row, LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(row, settings_details_menu_row_clicked, LV_EVENT_CLICKED, state);

        state->menu_titles[i] = settings_details_create_label(row,
                                                              settings_details_menu_items[i].title,
                                                              SETTINGS_DETAILS_MENU_LABEL_X,
                                                              SETTINGS_DETAILS_MENU_LABEL_Y,
                                                              SETTINGS_DETAILS_MENU_LABEL_WIDTH,
                                                              SETTINGS_DETAILS_MENU_LABEL_HEIGHT,
                                                              UI_STYLE_FONT_DETAILS_MENU_TITLE,
                                                              LV_TEXT_ALIGN_LEFT);
        if (state->menu_titles[i] == NULL) {
            return false;
        }
        lv_obj_add_flag(state->menu_titles[i], LV_OBJ_FLAG_CLICKABLE);
        lv_obj_add_event_cb(state->menu_titles[i], settings_details_menu_row_clicked, LV_EVENT_CLICKED, state);

        if (settings_details_menu_items[i].value[0] != '\0') {
            state->menu_values[i] = settings_details_create_label(row,
                                                                  settings_details_menu_items[i].value,
                                                                  SETTINGS_DETAILS_MENU_LABEL_X,
                                                                  SETTINGS_DETAILS_MENU_VALUE_Y,
                                                                  SETTINGS_DETAILS_MENU_LABEL_WIDTH,
                                                                  SETTINGS_DETAILS_MENU_LABEL_HEIGHT,
                                                                  UI_STYLE_FONT_DETAILS_MENU_VALUE,
                                                                  LV_TEXT_ALIGN_LEFT);
            if (state->menu_values[i] == NULL) {
                return false;
            }
            lv_obj_add_flag(state->menu_values[i], LV_OBJ_FLAG_CLICKABLE);
            lv_obj_add_event_cb(state->menu_values[i], settings_details_menu_row_clicked, LV_EVENT_CLICKED, state);
        }
    }

    settings_details_refresh_menu(state);
    return true;
}

static bool settings_details_create_content(settings_details_page_state_t *state)
{
    state->content = lv_obj_create(state->screen);
    if (state->content == NULL) {
        return false;
    }

    lv_obj_remove_style_all(state->content);
    lv_obj_set_size(state->content, SETTINGS_DETAILS_CONTENT_WIDTH, SETTINGS_DETAILS_CONTENT_HEIGHT);
    lv_obj_set_pos(state->content, SETTINGS_DETAILS_CONTENT_X, SETTINGS_DETAILS_CONTENT_Y);
    lv_obj_set_style_bg_color(state->content, lv_color_hex(SETTINGS_PAGE_BG_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(state->content, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_opa(state->content, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(state->content, LV_OPA_TRANSP, LV_PART_MAIN);

    return settings_details_create_content_for_tab(state);
}

static void settings_details_show_factory_modal(settings_details_page_state_t *state, bool visible)
{
    if (state == NULL || state->factory_modal == NULL) {
        return;
    }

    if (visible) {
        lv_obj_clear_flag(state->factory_modal, LV_OBJ_FLAG_HIDDEN);
        lv_obj_move_foreground(state->factory_modal);
    } else {
        lv_obj_add_flag(state->factory_modal, LV_OBJ_FLAG_HIDDEN);
    }
}

static void settings_details_factory_button_clicked(lv_event_t *event)
{
    settings_details_page_state_t *state;

    state = (settings_details_page_state_t *)lv_event_get_user_data(event);
    settings_details_show_factory_modal(state, true);
}

static void settings_details_factory_cancel_clicked(lv_event_t *event)
{
    settings_details_page_state_t *state;

    state = (settings_details_page_state_t *)lv_event_get_user_data(event);
    settings_details_show_factory_modal(state, false);
}

static void settings_details_factory_confirm_clicked(lv_event_t *event)
{
    settings_details_page_state_t *state;

    state = (settings_details_page_state_t *)lv_event_get_user_data(event);
    settings_details_show_factory_modal(state, false);
}

static bool settings_details_create_modal_button(lv_obj_t *parent,
                                                 settings_details_page_state_t *state,
                                                 const char *text,
                                                 int32_t x,
                                                 uint32_t color,
                                                 lv_event_cb_t clicked_cb)
{
    lv_obj_t *button;

    button = lv_button_create(parent);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_DETAILS_MODAL_BUTTON_WIDTH, SETTINGS_DETAILS_MODAL_BUTTON_HEIGHT);
    lv_obj_set_pos(button, x, SETTINGS_DETAILS_MODAL_BUTTON_Y);
    lv_obj_set_style_bg_color(button, lv_color_hex(color), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(button, SETTINGS_DETAILS_MODAL_BUTTON_RADIUS, LV_PART_MAIN);
    lv_obj_add_event_cb(button, clicked_cb, LV_EVENT_CLICKED, state);

    return settings_details_create_label(button,
                                         text,
                                         0,
                                         16,
                                         SETTINGS_DETAILS_MODAL_BUTTON_WIDTH,
                                         32,
                                         UI_STYLE_FONT_HOME_SIDE,
                                         LV_TEXT_ALIGN_CENTER) != NULL;
}

static bool settings_details_create_factory_modal(settings_details_page_state_t *state)
{
    lv_obj_t *modal;

    modal = lv_obj_create(state->screen);
    if (modal == NULL) {
        return false;
    }

    state->factory_modal = modal;
    lv_obj_remove_style_all(modal);
    lv_obj_set_size(modal, SETTINGS_PAGE_SCREEN_WIDTH, SETTINGS_PAGE_SCREEN_HEIGHT);
    lv_obj_set_pos(modal, 0, 0);
    lv_obj_set_style_bg_color(modal, lv_color_hex(SETTINGS_PAGE_BG_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(modal, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_add_flag(modal, LV_OBJ_FLAG_HIDDEN);

    if (settings_details_create_label(modal,
                                      "是否恢复出厂设置",
                                      SETTINGS_DETAILS_MODAL_TEXT_X,
                                      SETTINGS_DETAILS_MODAL_TEXT_Y,
                                      SETTINGS_DETAILS_MODAL_TEXT_WIDTH,
                                      SETTINGS_DETAILS_MODAL_TEXT_HEIGHT,
                                      UI_STYLE_FONT_DETAILS_MODAL,
                                      LV_TEXT_ALIGN_CENTER) == NULL ||
        !settings_details_create_modal_button(modal,
                                              state,
                                              "取消",
                                              SETTINGS_DETAILS_MODAL_CANCEL_X,
                                              SETTINGS_DETAILS_MODAL_CANCEL_COLOR,
                                              settings_details_factory_cancel_clicked) ||
        !settings_details_create_modal_button(modal,
                                              state,
                                              "确认",
                                              SETTINGS_DETAILS_MODAL_CONFIRM_X,
                                              SETTINGS_DETAILS_MODAL_CONFIRM_COLOR,
                                              settings_details_factory_confirm_clicked)) {
        return false;
    }

    return true;
}

void settings_details_page_destroy(page_manager_page_ctx_t *ctx)
{
    settings_details_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (settings_details_page_state_t *)lv_obj_get_user_data(ctx->screen);
    free(state);
}

lv_obj_t *settings_details_page_create(page_manager_page_ctx_t *ctx)
{
    lv_obj_t *screen;
    settings_details_page_state_t *state;

    (void)ctx;

    state = (settings_details_page_state_t *)calloc(1u, sizeof(*state));
    if (state == NULL) {
        return NULL;
    }

    screen = lv_obj_create(NULL);
    if (screen == NULL) {
        free(state);
        return NULL;
    }

    state->screen = screen;
    state->selected_tab = SETTINGS_DETAILS_TAB_DRINKS;
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
                                            settings_details_back_clicked) ||
        !settings_details_create_title(state) ||
        !settings_details_create_menu(state) ||
        !settings_details_create_content(state) ||
        !settings_details_create_factory_modal(state)) {
        lv_obj_delete(screen);
        free(state);
        return NULL;
    }

    return screen;
}

void settings_details_page_event(page_manager_page_ctx_t *ctx,
                                 uint32_t code,
                                 uint32_t wparam,
                                 uint32_t lparam)
{
    (void)ctx;
    (void)code;
    (void)wparam;
    (void)lparam;
}
