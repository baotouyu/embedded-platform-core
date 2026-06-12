#include "pages/settings_page.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "lvgl.h"
#include "multi_lang.h"
#include "pages/app_pages.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>

#define SETTINGS_PAGE_EVENT_REFRESH 1u

#define SETTINGS_PAGE_LANG_DB_NAME "recipelib.db"
#define SETTINGS_PAGE_LANGUAGE "zh-CN"
#define SETTINGS_PAGE_TITLE_KEY MULTI_LANG_KEY_SETTING

#define SETTINGS_PAGE_CONTENT_HEIGHT 696
#define SETTINGS_PAGE_BUTTON_BORDER_COLOR 0x666666

#define SETTINGS_PAGE_TITLE_Y 48
#define SETTINGS_PAGE_TITLE_HEIGHT 52

#define SETTINGS_PAGE_BUTTON_CONTAINER_Y 140
#define SETTINGS_PAGE_BUTTON_CONTAINER_HEIGHT (SETTINGS_PAGE_SCREEN_HEIGHT - SETTINGS_PAGE_BUTTON_CONTAINER_Y)
#define SETTINGS_PAGE_BUTTON_CONTENT_HEIGHT (SETTINGS_PAGE_CONTENT_HEIGHT - SETTINGS_PAGE_BUTTON_CONTAINER_Y)
#define SETTINGS_PAGE_BUTTON_WIDTH 356
#define SETTINGS_PAGE_BUTTON_HEIGHT 112
#define SETTINGS_PAGE_BUTTON_RADIUS 56
#define SETTINGS_PAGE_BUTTON_BORDER_WIDTH 2
#define SETTINGS_PAGE_BUTTON_GAP_X 40
#define SETTINGS_PAGE_BUTTON_GAP_Y 24
#define SETTINGS_PAGE_LEFT_X 24
#define SETTINGS_PAGE_RIGHT_X (SETTINGS_PAGE_LEFT_X + SETTINGS_PAGE_BUTTON_WIDTH + SETTINGS_PAGE_BUTTON_GAP_X)
#define SETTINGS_PAGE_ROW_0_Y 0
#define SETTINGS_PAGE_ROW_STEP (SETTINGS_PAGE_BUTTON_HEIGHT + SETTINGS_PAGE_BUTTON_GAP_Y)

#define SETTINGS_PAGE_ICON_X 16
#define SETTINGS_PAGE_ICON_Y 16
#define SETTINGS_PAGE_ICON_SIZE 80
#define SETTINGS_PAGE_LABEL_X 120
#define SETTINGS_PAGE_LABEL_Y 36
#define SETTINGS_PAGE_LABEL_WIDTH 220
#define SETTINGS_PAGE_LABEL_HEIGHT 40

typedef enum {
    SETTINGS_PAGE_ACTION_LANGUAGE = 0,
    SETTINGS_PAGE_ACTION_WIFI,
    SETTINGS_PAGE_ACTION_BRIGHTNESS,
    SETTINGS_PAGE_ACTION_VOLUME,
    SETTINGS_PAGE_ACTION_CLEAN,
    SETTINGS_PAGE_ACTION_SLEEP,
    SETTINGS_PAGE_ACTION_APP_LINK,
    SETTINGS_PAGE_ACTION_DETAILS,
} settings_page_action_t;

typedef struct {
    const char *text_key;
    const char *icon_name;
    int32_t x;
    int32_t y;
    settings_page_action_t action;
} settings_page_button_spec_t;

static const settings_page_button_spec_t settings_page_items[] = {
    {MULTI_LANG_KEY_LANGUAGE, "settings_icon_language.png", SETTINGS_PAGE_LEFT_X, SETTINGS_PAGE_ROW_0_Y,
     SETTINGS_PAGE_ACTION_LANGUAGE},
    {MULTI_LANG_KEY_WIFI, "settings_icon_wifi.png", SETTINGS_PAGE_RIGHT_X, SETTINGS_PAGE_ROW_0_Y,
     SETTINGS_PAGE_ACTION_WIFI},
    {MULTI_LANG_KEY_BRIGHTNESS, "settings_icon_brightness.png", SETTINGS_PAGE_LEFT_X,
     SETTINGS_PAGE_ROW_0_Y + SETTINGS_PAGE_ROW_STEP, SETTINGS_PAGE_ACTION_BRIGHTNESS},
    {MULTI_LANG_KEY_ON, "settings_icon_volume.png", SETTINGS_PAGE_RIGHT_X,
     SETTINGS_PAGE_ROW_0_Y + SETTINGS_PAGE_ROW_STEP, SETTINGS_PAGE_ACTION_VOLUME},
    {MULTI_LANG_KEY_RINSE, "settings_icon_clean.png", SETTINGS_PAGE_LEFT_X,
     SETTINGS_PAGE_ROW_0_Y + SETTINGS_PAGE_ROW_STEP * 2, SETTINGS_PAGE_ACTION_CLEAN},
    {MULTI_LANG_KEY_SLEEP, "settings_icon_sleep.png", SETTINGS_PAGE_RIGHT_X,
     SETTINGS_PAGE_ROW_0_Y + SETTINGS_PAGE_ROW_STEP * 2, SETTINGS_PAGE_ACTION_SLEEP},
    {MULTI_LANG_KEY_APP_LINK, "settings_icon_app_link.png", SETTINGS_PAGE_LEFT_X,
     SETTINGS_PAGE_ROW_0_Y + SETTINGS_PAGE_ROW_STEP * 3, SETTINGS_PAGE_ACTION_APP_LINK},
    {MULTI_LANG_KEY_DETAILS, "settings_icon_info.png", SETTINGS_PAGE_RIGHT_X,
     SETTINGS_PAGE_ROW_0_Y + SETTINGS_PAGE_ROW_STEP * 3, SETTINGS_PAGE_ACTION_DETAILS},
};

typedef struct {
    lv_obj_t *screen;
    lv_obj_t *button_container;
    multi_lang_store_t *lang_store;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char item_src[sizeof(settings_page_items) / sizeof(settings_page_items[0])][SETTINGS_PAGE_SRC_BUFFER_SIZE];
} settings_page_state_t;

static void settings_page_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static void settings_page_item_clicked(lv_event_t *event)
{
    const settings_page_button_spec_t *spec;

    spec = (const settings_page_button_spec_t *)lv_event_get_user_data(event);
    if (spec == NULL) {
        return;
    }

    if (spec->action == SETTINGS_PAGE_ACTION_LANGUAGE) {
        (void)page_manager_switch(APP_PAGE_LANGUAGE, LV_SCR_LOAD_ANIM_MOVE_LEFT, 180, true);
    } else if (spec->action == SETTINGS_PAGE_ACTION_BRIGHTNESS) {
        (void)page_manager_switch(APP_PAGE_BRIGHTNESS, LV_SCR_LOAD_ANIM_MOVE_LEFT, 180, true);
    } else if (spec->action == SETTINGS_PAGE_ACTION_SLEEP) {
        (void)page_manager_switch(APP_PAGE_SLEEP, LV_SCR_LOAD_ANIM_MOVE_LEFT, 180, true);
    }
}

static const char *settings_page_text(settings_page_state_t *state, const char *key)
{
    const char *text = key;

    if (state != NULL && state->lang_store != NULL &&
        multi_lang_get_text(state->lang_store, key, &text) == EP_OK) {
        return text;
    }

    return key;
}

static void settings_page_open_language(settings_page_state_t *state)
{
    char db_path[160];

    if (state == NULL) {
        return;
    }

    if (ep_platform_recipe_path(SETTINGS_PAGE_LANG_DB_NAME, db_path, sizeof(db_path)) != EP_OK) {
        return;
    }

    if (multi_lang_open_db(db_path, &state->lang_store) != EP_OK) {
        state->lang_store = NULL;
        return;
    }

    if (multi_lang_set_language(state->lang_store, SETTINGS_PAGE_LANGUAGE) != EP_OK) {
        multi_lang_close(state->lang_store);
        state->lang_store = NULL;
    }
}

static lv_obj_t *settings_page_create_button_container(lv_obj_t *screen)
{
    lv_obj_t *container;

    container = lv_obj_create(screen);
    if (container == NULL) {
        return NULL;
    }

    settings_common_style_screen(container);
    lv_obj_set_size(container, SETTINGS_PAGE_SCREEN_WIDTH, SETTINGS_PAGE_BUTTON_CONTAINER_HEIGHT);
    lv_obj_set_pos(container, 0, SETTINGS_PAGE_BUTTON_CONTAINER_Y);
    lv_obj_add_flag(container, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_scroll_dir(container, LV_DIR_VER);
    lv_obj_set_scrollbar_mode(container, LV_SCROLLBAR_MODE_OFF);

    return container;
}

static bool settings_page_create_title(settings_page_state_t *state)
{
    lv_obj_t *title;

    title = lv_label_create(state->screen);
    if (title == NULL) {
        return false;
    }

    lv_obj_remove_style_all(title);
    lv_obj_set_size(title, SETTINGS_PAGE_SCREEN_WIDTH, SETTINGS_PAGE_TITLE_HEIGHT);
    lv_obj_set_pos(title, 0, SETTINGS_PAGE_TITLE_Y);
    lv_obj_set_style_text_color(title, lv_color_hex(SETTINGS_PAGE_TEXT_COLOR), LV_PART_MAIN);
    lv_obj_set_style_text_font(title, ui_style_font(UI_STYLE_FONT_HOME_CENTER), LV_PART_MAIN);
    lv_obj_set_style_text_align(title, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_label_set_text(title, settings_page_text(state, SETTINGS_PAGE_TITLE_KEY));

    return true;
}

static bool settings_page_create_back_button(settings_page_state_t *state)
{
    return settings_common_create_icon_button(state->screen,
                                             SETTINGS_PAGE_BACK_ICON_NAME,
                                             state->back_src,
                                             sizeof(state->back_src),
                                             SETTINGS_PAGE_BACK_X,
                                             SETTINGS_PAGE_BACK_Y,
                                             SETTINGS_PAGE_BACK_SIZE,
                                             settings_page_back_clicked);
}

static bool settings_page_create_button(settings_page_state_t *state,
                                        const settings_page_button_spec_t *spec,
                                        size_t index)
{
    lv_obj_t *button;
    lv_obj_t *image;
    lv_obj_t *label;

    button = lv_button_create(state->button_container);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, SETTINGS_PAGE_BUTTON_WIDTH, SETTINGS_PAGE_BUTTON_HEIGHT);
    lv_obj_set_pos(button, spec->x, spec->y);
    lv_obj_set_style_bg_color(button, lv_color_hex(SETTINGS_PAGE_BUTTON_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(button, SETTINGS_PAGE_BUTTON_RADIUS, LV_PART_MAIN);
    lv_obj_set_style_border_width(button, SETTINGS_PAGE_BUTTON_BORDER_WIDTH, LV_PART_MAIN);
    lv_obj_set_style_border_color(button, lv_color_hex(SETTINGS_PAGE_BUTTON_BORDER_COLOR), LV_PART_MAIN);
    lv_obj_set_style_border_opa(button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_event_cb(button, settings_page_item_clicked, LV_EVENT_CLICKED, (void *)spec);

    if (ep_platform_lvgl_image_src(spec->icon_name, state->item_src[index], sizeof(state->item_src[index])) ==
        EP_OK) {
        image = lv_image_create(button);
        if (image == NULL) {
            return false;
        }

        lv_obj_remove_style_all(image);
        lv_obj_set_size(image, SETTINGS_PAGE_ICON_SIZE, SETTINGS_PAGE_ICON_SIZE);
        lv_obj_set_pos(image, SETTINGS_PAGE_ICON_X, SETTINGS_PAGE_ICON_Y);
        lv_image_set_src(image, state->item_src[index]);
    }

    label = lv_label_create(button);
    if (label == NULL) {
        return false;
    }

    lv_obj_remove_style_all(label);
    lv_obj_set_size(label, SETTINGS_PAGE_LABEL_WIDTH, SETTINGS_PAGE_LABEL_HEIGHT);
    lv_obj_set_pos(label, SETTINGS_PAGE_LABEL_X, SETTINGS_PAGE_LABEL_Y);
    lv_obj_set_style_text_color(label, lv_color_hex(SETTINGS_PAGE_TEXT_COLOR), LV_PART_MAIN);
    lv_obj_set_style_text_font(label, ui_style_font(UI_STYLE_FONT_HOME_USER), LV_PART_MAIN);
    lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_LEFT, LV_PART_MAIN);
    lv_label_set_long_mode(label, LV_LABEL_LONG_CLIP);
    lv_label_set_text(label, settings_page_text(state, spec->text_key));

    return true;
}

static bool settings_page_create_buttons(settings_page_state_t *state)
{
    size_t item_count;

    item_count = sizeof(settings_page_items) / sizeof(settings_page_items[0]);
    for (size_t i = 0; i < item_count; ++i) {
        if (!settings_page_create_button(state, &settings_page_items[i], i)) {
            return false;
        }
    }

    return true;
}

static bool settings_page_create_scroll_spacer(settings_page_state_t *state)
{
    lv_obj_t *spacer;

    spacer = lv_obj_create(state->button_container);
    if (spacer == NULL) {
        return false;
    }

    lv_obj_remove_style_all(spacer);
    lv_obj_set_size(spacer, 1, 1);
    lv_obj_set_pos(spacer, 0, SETTINGS_PAGE_BUTTON_CONTENT_HEIGHT - 1);
    lv_obj_set_style_bg_opa(spacer, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_clear_flag(spacer, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLLABLE);

    return true;
}

static void settings_page_close_state(settings_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    if (state->lang_store != NULL) {
        multi_lang_close(state->lang_store);
        state->lang_store = NULL;
    }
}

void settings_page_destroy(page_manager_page_ctx_t *ctx)
{
    settings_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (settings_page_state_t *)lv_obj_get_user_data(ctx->screen);
    settings_page_close_state(state);
    free(state);
}

lv_obj_t *settings_page_create(page_manager_page_ctx_t *ctx)
{
    lv_obj_t *screen;
    settings_page_state_t *state;

    (void)ctx;

    state = (settings_page_state_t *)calloc(1u, sizeof(*state));
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
    settings_page_open_language(state);
    settings_common_style_screen(screen);

    state->button_container = settings_page_create_button_container(screen);
    if (state->button_container == NULL ||
        !settings_page_create_back_button(state) ||
        !settings_page_create_title(state) ||
        !settings_page_create_buttons(state) ||
        !settings_page_create_scroll_spacer(state)) {
        lv_obj_delete(screen);
        settings_page_close_state(state);
        free(state);
        return NULL;
    }

    return screen;
}

void settings_page_event(page_manager_page_ctx_t *ctx,
                         uint32_t code,
                         uint32_t wparam,
                         uint32_t lparam)
{
    (void)ctx;
    (void)wparam;
    (void)lparam;

    if (code == SETTINGS_PAGE_EVENT_REFRESH) {
        return;
    }
}
