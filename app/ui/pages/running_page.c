#include "pages/running_page.h"

#include "lvgl.h"
#include "pages/settings_common.h"

#include <stdlib.h>

typedef struct {
    lv_obj_t *screen;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
} running_page_state_t;

static void running_page_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
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
    lv_obj_set_user_data(screen, state);
    settings_common_style_screen(screen);

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
