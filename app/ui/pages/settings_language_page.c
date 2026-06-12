#include "pages/settings_page.h"

#include "lvgl.h"
#include "multi_lang.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stdlib.h>

#define SETTINGS_LANGUAGE_TITLE_TEXT "语言"
#define SETTINGS_PAGE_LANGUAGE "zh-CN"

static const settings_selection_option_t settings_language_options[] = {
    {"English", "en"},
    {"简体中文", "zh-CN"},
    {"Français", "fr"},
    {"Italiano", "it"},
    {"Deutsch", "de"},
    {"Русский", "ru"},
};

static void settings_language_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static void settings_language_confirm_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static bool settings_language_create_title(settings_selection_page_state_t *state)
{
    return state != NULL && settings_common_create_title(state->screen, SETTINGS_LANGUAGE_TITLE_TEXT);
}

void settings_language_page_destroy(page_manager_page_ctx_t *ctx)
{
    settings_selection_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (settings_selection_page_state_t *)lv_obj_get_user_data(ctx->screen);
    if (state == NULL) {
        return;
    }

    settings_selection_list_release(&state->list);
    free(state);
}

lv_obj_t *settings_language_page_create(page_manager_page_ctx_t *ctx)
{
    lv_obj_t *screen;
    settings_selection_page_state_t *state;

    (void)ctx;

    state = (settings_selection_page_state_t *)calloc(1u, sizeof(*state));
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
    settings_common_style_screen(screen);

    if (!settings_common_create_icon_button(screen,
                                            SETTINGS_PAGE_BACK_ICON_NAME,
                                            state->back_src,
                                            sizeof(state->back_src),
                                            SETTINGS_PAGE_BACK_X,
                                            SETTINGS_PAGE_BACK_Y,
                                            SETTINGS_PAGE_BACK_SIZE,
                                            settings_language_back_clicked) ||
        !settings_common_create_icon_button(screen,
                                            SETTINGS_PAGE_CONFIRM_ICON_NAME,
                                            state->confirm_src,
                                            sizeof(state->confirm_src),
                                            SETTINGS_PAGE_CONFIRM_X,
                                            SETTINGS_PAGE_CONFIRM_Y,
                                            SETTINGS_PAGE_CONFIRM_SIZE,
                                            settings_language_confirm_clicked) ||
        !settings_language_create_title(state) ||
        !settings_selection_list_create(screen,
                                        &state->list,
                                        settings_language_options,
                                        sizeof(settings_language_options) / sizeof(settings_language_options[0]),
                                        settings_selection_option_index(settings_language_options,
                                                                        sizeof(settings_language_options) /
                                                                            sizeof(settings_language_options[0]),
                                                                        SETTINGS_PAGE_LANGUAGE),
                                        SETTINGS_SELECTION_LIST_X,
                                        SETTINGS_SELECTION_LIST_Y,
                                        SETTINGS_SELECTION_LIST_VISIBLE_ROWS)) {
        lv_obj_delete(screen);
        settings_selection_list_release(&state->list);
        free(state);
        return NULL;
    }

    return screen;
}

void settings_language_page_event(page_manager_page_ctx_t *ctx,
                                  uint32_t code,
                                  uint32_t wparam,
                                  uint32_t lparam)
{
    (void)ctx;
    (void)code;
    (void)wparam;
    (void)lparam;
}
