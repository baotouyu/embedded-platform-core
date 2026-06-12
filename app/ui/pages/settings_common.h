#ifndef SETTINGS_COMMON_H
#define SETTINGS_COMMON_H

#include "lvgl.h"
#include "page_manager.h"

#include <stdbool.h>
#include <stddef.h>

#define SETTINGS_PAGE_SCREEN_WIDTH 800
#define SETTINGS_PAGE_SCREEN_HEIGHT 480
#define SETTINGS_PAGE_BG_COLOR 0x000000
#define SETTINGS_PAGE_BUTTON_COLOR 0x2F2B29
#define SETTINGS_SHARED_GRAY_BORDER_COLOR 0x666666
#define SETTINGS_PAGE_TEXT_COLOR 0xFFFFFF

#define SETTINGS_PAGE_BACK_ICON_NAME "settings_icon_back.png"
#define SETTINGS_PAGE_CONFIRM_ICON_NAME "settings_icon_confirm.png"
#define SETTINGS_PAGE_BACK_X 32
#define SETTINGS_PAGE_BACK_Y 32
#define SETTINGS_PAGE_BACK_SIZE 48
#define SETTINGS_PAGE_CONFIRM_X 720
#define SETTINGS_PAGE_CONFIRM_Y 32
#define SETTINGS_PAGE_CONFIRM_SIZE 48
#define SETTINGS_PAGE_SRC_BUFFER_SIZE 128
#define SETTINGS_SUBPAGE_TITLE_X 0
#define SETTINGS_SUBPAGE_TITLE_Y 90
#define SETTINGS_SUBPAGE_TITLE_WIDTH SETTINGS_PAGE_SCREEN_WIDTH
#define SETTINGS_SUBPAGE_TITLE_HEIGHT 42

#define SETTINGS_SELECTION_LIST_WIDTH 369
#define SETTINGS_SELECTION_LIST_ROW_HEIGHT 64
#define SETTINGS_SELECTION_LIST_RADIUS 12
#define SETTINGS_SELECTION_LIST_X ((SETTINGS_PAGE_SCREEN_WIDTH - SETTINGS_SELECTION_LIST_WIDTH) / 2)
#define SETTINGS_SELECTION_LIST_Y 160
#define SETTINGS_SELECTION_LIST_VISIBLE_ROWS 5
#define SETTINGS_SELECTION_LIST_UNSELECTED_COLOR SETTINGS_PAGE_BUTTON_COLOR
#define SETTINGS_SELECTION_LIST_SELECTED_COLOR 0xFFFFFF
#define SETTINGS_SELECTION_LIST_SEPARATOR_COLOR 0x3A3A3A

typedef struct {
    const char *label;
    const char *value;
} settings_selection_option_t;

typedef struct {
    lv_obj_t *container;
    lv_obj_t **rows;
    lv_obj_t **labels;
    size_t option_count;
    size_t selected_index;
} settings_selection_list_t;

typedef struct {
    lv_obj_t *screen;
    settings_selection_list_t list;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char confirm_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
} settings_selection_page_state_t;

void settings_common_style_screen(lv_obj_t *screen);
bool settings_common_create_icon_button(lv_obj_t *screen,
                                        const char *icon_name,
                                        char *src,
                                        size_t src_size,
                                        int32_t x,
                                        int32_t y,
                                        int32_t size,
                                        lv_event_cb_t clicked_cb);
bool settings_common_create_title(lv_obj_t *screen, const char *text);
bool settings_selection_list_create(lv_obj_t *parent,
                                    settings_selection_list_t *list,
                                    const settings_selection_option_t *options,
                                    size_t option_count,
                                    size_t selected_index,
                                    int32_t x,
                                    int32_t y,
                                    int32_t visible_rows);
void settings_selection_list_refresh(settings_selection_list_t *list);
void settings_selection_list_release(settings_selection_list_t *list);
size_t settings_selection_option_index(const settings_selection_option_t *options,
                                       size_t option_count,
                                       const char *value);

#endif
