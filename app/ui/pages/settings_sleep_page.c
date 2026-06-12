#include "pages/settings_page.h"

#include "lvgl.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stdlib.h>

#define SETTINGS_SLEEP_DEFAULT_VALUE "30mins"
#define SETTINGS_SLEEP_VISIBLE_ROWS 4

static const settings_selection_option_t settings_sleep_options[] = {
    {"10mins", "10mins"},
    {"30mins", "30mins"},
    {"1h", "1h"},
    {"2h", "2h"},
};

static const size_t settings_sleep_default_index = 1u;

static void settings_sleep_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

static void settings_sleep_confirm_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

void settings_sleep_page_destroy(page_manager_page_ctx_t *ctx)
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

lv_obj_t *settings_sleep_page_create(page_manager_page_ctx_t *ctx)
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
                                            settings_sleep_back_clicked) ||
        !settings_common_create_icon_button(screen,
                                            SETTINGS_PAGE_CONFIRM_ICON_NAME,
                                            state->confirm_src,
                                            sizeof(state->confirm_src),
                                            SETTINGS_PAGE_CONFIRM_X,
                                            SETTINGS_PAGE_CONFIRM_Y,
                                            SETTINGS_PAGE_CONFIRM_SIZE,
                                            settings_sleep_confirm_clicked) ||
        !settings_selection_list_create(screen,
                                        &state->list,
                                        settings_sleep_options,
                                        sizeof(settings_sleep_options) / sizeof(settings_sleep_options[0]),
                                        settings_selection_option_index(settings_sleep_options,
                                                                        sizeof(settings_sleep_options) /
                                                                            sizeof(settings_sleep_options[0]),
                                                                        SETTINGS_SLEEP_DEFAULT_VALUE),
                                        SETTINGS_SELECTION_LIST_X,
                                        SETTINGS_SELECTION_LIST_Y,
                                        SETTINGS_SLEEP_VISIBLE_ROWS)) {
        lv_obj_delete(screen);
        settings_selection_list_release(&state->list);
        free(state);
        return NULL;
    }

    if (state->list.selected_index >= sizeof(settings_sleep_options) / sizeof(settings_sleep_options[0])) {
        state->list.selected_index = settings_sleep_default_index;
        settings_selection_list_refresh(&state->list);
    }

    return screen;
}

void settings_sleep_page_event(page_manager_page_ctx_t *ctx,
                               uint32_t code,
                               uint32_t wparam,
                               uint32_t lparam)
{
    (void)ctx;
    (void)code;
    (void)wparam;
    (void)lparam;
}
