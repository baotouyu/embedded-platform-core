#include "pages/settings_common.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "ui_style.h"

#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

void settings_common_style_screen(lv_obj_t *screen)
{
    lv_obj_remove_style_all(screen);
    lv_obj_set_style_bg_color(screen, lv_color_hex(SETTINGS_PAGE_BG_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(screen, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_opa(screen, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(screen, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_size(screen, SETTINGS_PAGE_SCREEN_WIDTH, SETTINGS_PAGE_SCREEN_HEIGHT);
    lv_obj_clear_flag(screen, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_scrollbar_mode(screen, LV_SCROLLBAR_MODE_OFF);
}

bool settings_common_create_icon_button(lv_obj_t *screen,
                                        const char *icon_name,
                                        char *src,
                                        size_t src_size,
                                        int32_t x,
                                        int32_t y,
                                        int32_t size,
                                        lv_event_cb_t clicked_cb)
{
    lv_obj_t *button;
    lv_obj_t *image;

    button = lv_button_create(screen);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, size, size);
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
    lv_obj_set_size(image, size, size);
    lv_obj_set_pos(image, 0, 0);
    lv_image_set_src(image, src);

    return true;
}

bool settings_common_create_title(lv_obj_t *screen, const char *text)
{
    lv_obj_t *title;

    if (screen == NULL || text == NULL) {
        return false;
    }

    title = lv_label_create(screen);
    if (title == NULL) {
        return false;
    }

    lv_obj_remove_style_all(title);
    lv_obj_set_size(title, SETTINGS_SUBPAGE_TITLE_WIDTH, SETTINGS_SUBPAGE_TITLE_HEIGHT);
    lv_obj_set_pos(title, SETTINGS_SUBPAGE_TITLE_X, SETTINGS_SUBPAGE_TITLE_Y);
    lv_obj_set_style_text_color(title, lv_color_hex(SETTINGS_PAGE_TEXT_COLOR), LV_PART_MAIN);
    lv_obj_set_style_text_font(title, ui_style_font(UI_STYLE_FONT_HOME_USER), LV_PART_MAIN);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_label_set_long_mode(title, LV_LABEL_LONG_CLIP);
    lv_label_set_text(title, text);

    return true;
}

void settings_selection_list_refresh(settings_selection_list_t *list)
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
            lv_obj_set_style_text_color(
                list->labels[i],
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

bool settings_selection_list_create(lv_obj_t *parent,
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
        settings_selection_list_release(list);
        return false;
    }

    list->option_count = option_count;
    list->selected_index = selected_index < option_count ? selected_index : 0u;
    visible_height = SETTINGS_SELECTION_LIST_ROW_HEIGHT * visible_rows;

    list->container = lv_obj_create(parent);
    if (list->container == NULL) {
        settings_selection_list_release(list);
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
        lv_obj_t *row;
        lv_obj_t *label;

        row = lv_obj_create(list->container);
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
        lv_obj_set_style_text_font(label, ui_style_font(UI_STYLE_FONT_HOME_SIDE), LV_PART_MAIN);
        lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
        lv_obj_set_style_pad_top(label, 8, LV_PART_MAIN);
        lv_label_set_long_mode(label, LV_LABEL_LONG_CLIP);
        lv_label_set_text(label, options[i].label);
    }

    settings_selection_list_refresh(list);
    return true;
}

void settings_selection_list_release(settings_selection_list_t *list)
{
    if (list == NULL) {
        return;
    }

    free(list->rows);
    free(list->labels);
    list->rows = NULL;
    list->labels = NULL;
    list->container = NULL;
    list->option_count = 0u;
    list->selected_index = 0u;
}

size_t settings_selection_option_index(const settings_selection_option_t *options,
                                       size_t option_count,
                                       const char *value)
{
    if (options == NULL || value == NULL) {
        return 0u;
    }

    for (size_t i = 0u; i < option_count; ++i) {
        const char *candidate = options[i].value;

        if (candidate != NULL && strcmp(candidate, value) == 0) {
            return i;
        }
    }

    return 0u;
}
