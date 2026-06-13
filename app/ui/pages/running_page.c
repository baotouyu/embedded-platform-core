#include "pages/running_page.h"

#include "lvgl.h"
#include "pages/settings_common.h"

#include <stdio.h>
#include <stdlib.h>

#define RUNNING_PAGE_SRC_BUFFER_SIZE 160
#define RUNNING_PAGE_RECIPE_IMAGE_X 54
#define RUNNING_PAGE_RECIPE_IMAGE_Y 180
#define RUNNING_PAGE_RECIPE_IMAGE_SIZE 180
#define RUNNING_PAGE_IMAGE_SCALE_BASE 256u

typedef struct {
    lv_obj_t *screen;
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char recipe_image_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
} running_page_state_t;

static char running_page_pending_recipe_image_src[RUNNING_PAGE_SRC_BUFFER_SIZE];

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

void running_page_set_recipe_image_src(const char *src)
{
    running_page_copy_string(running_page_pending_recipe_image_src,
                             sizeof(running_page_pending_recipe_image_src),
                             src);
}

static void running_page_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
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

static void running_page_create_recipe_image(running_page_state_t *state)
{
    lv_image_header_t header;
    lv_obj_t *image;

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

    lv_image_set_src(image, state->recipe_image_src);
    lv_image_set_pivot(image, 0, 0);
    lv_image_set_scale(image, running_page_recipe_image_scale(&header));
    lv_obj_set_pos(image, RUNNING_PAGE_RECIPE_IMAGE_X, RUNNING_PAGE_RECIPE_IMAGE_Y);
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
    running_page_copy_string(state->recipe_image_src,
                             sizeof(state->recipe_image_src),
                             running_page_pending_recipe_image_src);
    lv_obj_set_user_data(screen, state);
    settings_common_style_screen(screen);
    running_page_create_recipe_image(state);

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
