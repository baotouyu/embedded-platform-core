#include "pages/running_page.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "lvgl.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define RUNNING_PAGE_SRC_BUFFER_SIZE 160
#define RUNNING_PAGE_BG_IMAGE_NAME "running_bg.png"
#define RUNNING_PAGE_STRENGTH_MINUS_ICON_NAME "running_minus.png"
#define RUNNING_PAGE_STRENGTH_PLUS_ICON_NAME "running_plus.png"
#define RUNNING_PAGE_STRENGTH_RING_BASE_IMAGE_NAME "running_ring_base.png"
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_IMAGE_NAME "running_ring_light.png"
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_IMAGE_NAME "running_ring_medium.png"
#define RUNNING_PAGE_STRENGTH_RING_STRONG_IMAGE_NAME "running_ring_strong.png"
#define RUNNING_PAGE_RECIPE_IMAGE_X 54
#define RUNNING_PAGE_RECIPE_IMAGE_Y 168
#define RUNNING_PAGE_RECIPE_IMAGE_SIZE 180
#define RUNNING_PAGE_IMAGE_SCALE_BASE 256u
#define RUNNING_PAGE_STRENGTH_TEXT_X 176
#define RUNNING_PAGE_STRENGTH_TEXT_Y 136
#define RUNNING_PAGE_STRENGTH_TEXT_WIDTH 80
#define RUNNING_PAGE_STRENGTH_TEXT_HEIGHT 44
#define RUNNING_PAGE_STRENGTH_BUTTON_Y 112
#define RUNNING_PAGE_STRENGTH_MINUS_X 32
#define RUNNING_PAGE_STRENGTH_PLUS_X 296
#define RUNNING_PAGE_STRENGTH_BUTTON_SIZE 44
#define RUNNING_PAGE_STRENGTH_RING_X 70
#define RUNNING_PAGE_STRENGTH_RING_Y 300
#define RUNNING_PAGE_STRENGTH_RING_WIDTH 160
#define RUNNING_PAGE_STRENGTH_RING_HEIGHT 80
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_X (RUNNING_PAGE_STRENGTH_RING_X + 84)
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_Y RUNNING_PAGE_STRENGTH_RING_Y
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_WIDTH 76
#define RUNNING_PAGE_STRENGTH_RING_LIGHT_HEIGHT 66
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_X (RUNNING_PAGE_STRENGTH_RING_X + 26)
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_Y RUNNING_PAGE_STRENGTH_RING_Y
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_WIDTH 134
#define RUNNING_PAGE_STRENGTH_RING_MEDIUM_HEIGHT 80
#define RUNNING_PAGE_STRENGTH_RING_STRONG_X RUNNING_PAGE_STRENGTH_RING_X
#define RUNNING_PAGE_STRENGTH_RING_STRONG_Y RUNNING_PAGE_STRENGTH_RING_Y
#define RUNNING_PAGE_STRENGTH_RING_STRONG_WIDTH 160
#define RUNNING_PAGE_STRENGTH_RING_STRONG_HEIGHT 80

typedef enum {
    RUNNING_PAGE_STRENGTH_LIGHT = 0,
    RUNNING_PAGE_STRENGTH_MEDIUM,
    RUNNING_PAGE_STRENGTH_STRONG,
} running_page_strength_t;

#define RUNNING_PAGE_STRENGTH_DEFAULT RUNNING_PAGE_STRENGTH_MEDIUM

typedef struct {
    lv_obj_t *screen;
    lv_obj_t *strength_label;
    lv_obj_t *strength_overlay;
    char bg_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char back_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char strength_minus_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_plus_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_ring_base_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_ring_light_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_ring_medium_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char strength_ring_strong_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    char recipe_image_src[RUNNING_PAGE_SRC_BUFFER_SIZE];
    running_page_strength_t strength;
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

static const char *running_page_strength_text(running_page_strength_t strength)
{
    if (strength == RUNNING_PAGE_STRENGTH_LIGHT) {
        return "清淡";
    }

    if (strength == RUNNING_PAGE_STRENGTH_STRONG) {
        return "浓郁";
    }

    return "适中";
}

static void running_page_refresh_strength(running_page_state_t *state)
{
    if (state == NULL) {
        return;
    }

    if (state->strength_label != NULL) {
        lv_label_set_text(state->strength_label, running_page_strength_text(state->strength));
    }

    if (state->strength_overlay == NULL) {
        return;
    }

    lv_obj_clear_flag(state->strength_overlay, LV_OBJ_FLAG_HIDDEN);
    if (state->strength == RUNNING_PAGE_STRENGTH_LIGHT) {
        lv_obj_set_pos(state->strength_overlay, RUNNING_PAGE_STRENGTH_RING_LIGHT_X, RUNNING_PAGE_STRENGTH_RING_LIGHT_Y);
        lv_obj_set_size(state->strength_overlay,
                        RUNNING_PAGE_STRENGTH_RING_LIGHT_WIDTH,
                        RUNNING_PAGE_STRENGTH_RING_LIGHT_HEIGHT);
        lv_image_set_src(state->strength_overlay, state->strength_ring_light_src);
    } else if (state->strength == RUNNING_PAGE_STRENGTH_MEDIUM) {
        lv_obj_set_pos(state->strength_overlay, RUNNING_PAGE_STRENGTH_RING_MEDIUM_X, RUNNING_PAGE_STRENGTH_RING_MEDIUM_Y);
        lv_obj_set_size(state->strength_overlay,
                        RUNNING_PAGE_STRENGTH_RING_MEDIUM_WIDTH,
                        RUNNING_PAGE_STRENGTH_RING_MEDIUM_HEIGHT);
        lv_image_set_src(state->strength_overlay, state->strength_ring_medium_src);
    } else {
        lv_obj_set_pos(state->strength_overlay, RUNNING_PAGE_STRENGTH_RING_STRONG_X, RUNNING_PAGE_STRENGTH_RING_STRONG_Y);
        lv_obj_set_size(state->strength_overlay,
                        RUNNING_PAGE_STRENGTH_RING_STRONG_WIDTH,
                        RUNNING_PAGE_STRENGTH_RING_STRONG_HEIGHT);
        lv_image_set_src(state->strength_overlay, state->strength_ring_strong_src);
    }
}

static void running_page_strength_minus_clicked(lv_event_t *event)
{
    running_page_state_t *state;

    state = (running_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL || state->strength == RUNNING_PAGE_STRENGTH_LIGHT) {
        return;
    }

    state->strength = (running_page_strength_t)(state->strength - 1);
    running_page_refresh_strength(state);
}

static void running_page_strength_plus_clicked(lv_event_t *event)
{
    running_page_state_t *state;

    state = (running_page_state_t *)lv_event_get_user_data(event);
    if (state == NULL || state->strength == RUNNING_PAGE_STRENGTH_STRONG) {
        return;
    }

    state->strength = (running_page_strength_t)(state->strength + 1);
    running_page_refresh_strength(state);
}

static void running_page_create_background(running_page_state_t *state)
{
    lv_obj_t *bg;

    if (state == NULL || state->screen == NULL) {
        return;
    }

    if (ep_platform_lvgl_image_src(RUNNING_PAGE_BG_IMAGE_NAME,
                                   state->bg_src,
                                   sizeof(state->bg_src)) != EP_OK) {
        return;
    }

    bg = lv_image_create(state->screen);
    if (bg == NULL) {
        return;
    }

    lv_image_set_src(bg, state->bg_src);
    lv_obj_set_size(bg, SETTINGS_PAGE_SCREEN_WIDTH, SETTINGS_PAGE_SCREEN_HEIGHT);
    lv_obj_set_pos(bg, 0, 0);
    lv_obj_move_background(bg);
}

static bool running_page_create_image(lv_obj_t *parent,
                                      const char *src,
                                      int32_t x,
                                      int32_t y,
                                      int32_t width,
                                      int32_t height,
                                      lv_obj_t **out_image)
{
    lv_obj_t *image;

    if (parent == NULL || src == NULL || src[0] == '\0') {
        return false;
    }

    image = lv_image_create(parent);
    if (image == NULL) {
        return false;
    }

    lv_image_set_src(image, src);
    lv_obj_set_size(image, width, height);
    lv_obj_set_pos(image, x, y);

    if (out_image != NULL) {
        *out_image = image;
    }

    return true;
}

static bool running_page_create_strength_button(running_page_state_t *state,
                                                const char *icon_name,
                                                char *src,
                                                size_t src_size,
                                                int32_t x,
                                                lv_event_cb_t clicked_cb)
{
    lv_obj_t *button;
    lv_obj_t *icon;

    if (state == NULL || state->screen == NULL) {
        return false;
    }

    button = lv_button_create(state->screen);
    if (button == NULL) {
        return false;
    }

    lv_obj_remove_style_all(button);
    lv_obj_set_size(button, RUNNING_PAGE_STRENGTH_BUTTON_SIZE, RUNNING_PAGE_STRENGTH_BUTTON_SIZE);
    lv_obj_set_pos(button, x, RUNNING_PAGE_STRENGTH_BUTTON_Y);
    lv_obj_set_style_bg_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_border_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(button, LV_OPA_TRANSP, LV_PART_MAIN);
    lv_obj_add_event_cb(button, clicked_cb, LV_EVENT_CLICKED, state);

    if (ep_platform_lvgl_image_src(icon_name, src, src_size) != EP_OK) {
        return true;
    }

    icon = lv_image_create(button);
    if (icon == NULL) {
        return false;
    }

    lv_obj_remove_style_all(icon);
    lv_obj_set_size(icon, RUNNING_PAGE_STRENGTH_BUTTON_SIZE, RUNNING_PAGE_STRENGTH_BUTTON_SIZE);
    lv_obj_set_pos(icon, 0, 0);
    lv_image_set_src(icon, src);

    return true;
}

static void running_page_create_strength_ring(running_page_state_t *state)
{
    if (state == NULL || state->screen == NULL) {
        return;
    }

    if (ep_platform_lvgl_image_src(RUNNING_PAGE_STRENGTH_RING_BASE_IMAGE_NAME,
                                   state->strength_ring_base_src,
                                   sizeof(state->strength_ring_base_src)) == EP_OK) {
        (void)running_page_create_image(state->screen,
                                        state->strength_ring_base_src,
                                        RUNNING_PAGE_STRENGTH_RING_X,
                                        RUNNING_PAGE_STRENGTH_RING_Y,
                                        RUNNING_PAGE_STRENGTH_RING_WIDTH,
                                        RUNNING_PAGE_STRENGTH_RING_HEIGHT,
                                        NULL);
    }

    (void)ep_platform_lvgl_image_src(RUNNING_PAGE_STRENGTH_RING_LIGHT_IMAGE_NAME,
                                     state->strength_ring_light_src,
                                     sizeof(state->strength_ring_light_src));
    (void)ep_platform_lvgl_image_src(RUNNING_PAGE_STRENGTH_RING_MEDIUM_IMAGE_NAME,
                                     state->strength_ring_medium_src,
                                     sizeof(state->strength_ring_medium_src));
    (void)ep_platform_lvgl_image_src(RUNNING_PAGE_STRENGTH_RING_STRONG_IMAGE_NAME,
                                     state->strength_ring_strong_src,
                                     sizeof(state->strength_ring_strong_src));

    (void)running_page_create_image(state->screen,
                                    state->strength_ring_medium_src,
                                    RUNNING_PAGE_STRENGTH_RING_MEDIUM_X,
                                    RUNNING_PAGE_STRENGTH_RING_MEDIUM_Y,
                                    RUNNING_PAGE_STRENGTH_RING_MEDIUM_WIDTH,
                                    RUNNING_PAGE_STRENGTH_RING_MEDIUM_HEIGHT,
                                    &state->strength_overlay);
    running_page_refresh_strength(state);
}

static void running_page_create_strength_controls(running_page_state_t *state)
{
    if (state == NULL || state->screen == NULL) {
        return;
    }

    (void)running_page_create_strength_button(state,
                                              RUNNING_PAGE_STRENGTH_MINUS_ICON_NAME,
                                              state->strength_minus_src,
                                              sizeof(state->strength_minus_src),
                                              RUNNING_PAGE_STRENGTH_MINUS_X,
                                              running_page_strength_minus_clicked);
    (void)running_page_create_strength_button(state,
                                              RUNNING_PAGE_STRENGTH_PLUS_ICON_NAME,
                                              state->strength_plus_src,
                                              sizeof(state->strength_plus_src),
                                              RUNNING_PAGE_STRENGTH_PLUS_X,
                                              running_page_strength_plus_clicked);

    state->strength_label = lv_label_create(state->screen);
    if (state->strength_label != NULL) {
        lv_obj_remove_style_all(state->strength_label);
        lv_obj_set_size(state->strength_label,
                        RUNNING_PAGE_STRENGTH_TEXT_WIDTH,
                        RUNNING_PAGE_STRENGTH_TEXT_HEIGHT);
        lv_obj_set_pos(state->strength_label,
                       RUNNING_PAGE_STRENGTH_TEXT_X - RUNNING_PAGE_STRENGTH_TEXT_WIDTH / 2,
                       RUNNING_PAGE_STRENGTH_TEXT_Y);
        lv_obj_set_style_text_color(state->strength_label, lv_color_white(), LV_PART_MAIN);
        lv_obj_set_style_text_font(state->strength_label, ui_style_font(UI_STYLE_FONT_HOME_USER), LV_PART_MAIN);
        lv_obj_set_style_text_align(state->strength_label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
        lv_label_set_long_mode(state->strength_label, LV_LABEL_LONG_CLIP);
    }

    running_page_refresh_strength(state);
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
    state->strength = RUNNING_PAGE_STRENGTH_DEFAULT;
    running_page_copy_string(state->recipe_image_src,
                             sizeof(state->recipe_image_src),
                             running_page_pending_recipe_image_src);
    lv_obj_set_user_data(screen, state);
    settings_common_style_screen(screen);
    running_page_create_background(state);
    running_page_create_strength_ring(state);
    running_page_create_recipe_image(state);
    running_page_create_strength_controls(state);

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
