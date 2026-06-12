#include "pages/boot_page.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "lvgl.h"
#include "pages/app_pages.h"
#include "pages/settings_common.h"
#include "ui_style.h"

#include <stddef.h>
#include <stdlib.h>

#define BOOT_PAGE_LOGO_IMAGE_NAME "boot_logo.png"
#define BOOT_PAGE_SPINNER_IMAGE_NAME "boot_loading.png"
#define BOOT_PAGE_DONE_IMAGE_NAME "boot_done.png"

#define BOOT_PAGE_LOGO_DELAY_MS 2000u
#define BOOT_PAGE_STAGE_DELAY_MS 2000u
#define BOOT_PAGE_SPINNER_PERIOD_MS 80u
#define BOOT_PAGE_SPINNER_STEP_DEG 300

#define BOOT_PAGE_LOGO_WIDTH 384
#define BOOT_PAGE_LOGO_HEIGHT 76
#define BOOT_PAGE_LOGO_X ((SETTINGS_PAGE_SCREEN_WIDTH - BOOT_PAGE_LOGO_WIDTH) / 2)
#define BOOT_PAGE_LOGO_Y 202

#define BOOT_PAGE_STAGE_COUNT 4u
#define BOOT_PAGE_STAGE_CARD_WIDTH 144
#define BOOT_PAGE_STAGE_CARD_HEIGHT 155
#define BOOT_PAGE_STAGE_CARD_RADIUS 16
#define BOOT_PAGE_STAGE_CARD_BORDER_WIDTH 1
#define BOOT_PAGE_STAGE_BORDER_COLOR 0x666666
#define BOOT_PAGE_STAGE_CARD_Y 163
#define BOOT_PAGE_STAGE_FIRST_X 76
#define BOOT_PAGE_STAGE_GAP 24
#define BOOT_PAGE_STAGE_ICON_SIZE 48
#define BOOT_PAGE_STAGE_ICON_X ((BOOT_PAGE_STAGE_CARD_WIDTH - BOOT_PAGE_STAGE_ICON_SIZE) / 2)
#define BOOT_PAGE_STAGE_ICON_Y 24
#define BOOT_PAGE_STAGE_TEXT_CONTAINER_X 12
#define BOOT_PAGE_STAGE_TEXT_CONTAINER_Y 94
#define BOOT_PAGE_STAGE_TEXT_CONTAINER_WIDTH 120
#define BOOT_PAGE_STAGE_TEXT_CONTAINER_HEIGHT 40

typedef enum {
    BOOT_PAGE_PHASE_LOGO = 0,
    BOOT_PAGE_PHASE_STAGES,
} boot_page_phase_t;

typedef struct {
    const char *label;
} boot_stage_t;

typedef struct {
    lv_obj_t *screen;
    lv_obj_t *logo;
    lv_obj_t *stage_cards[BOOT_PAGE_STAGE_COUNT];
    lv_obj_t *stage_icon_holders[BOOT_PAGE_STAGE_COUNT];
    lv_obj_t *stage_icons[BOOT_PAGE_STAGE_COUNT];
    lv_timer_t *timer;
    lv_timer_t *spinner_timer;
    boot_page_phase_t phase;
    size_t active_stage;
    int32_t spinner_rotation;
    char logo_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char spinner_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
    char done_src[SETTINGS_PAGE_SRC_BUFFER_SIZE];
} boot_page_state_t;

static const boot_stage_t boot_page_stages[] = {
    {"自检"},
    {"加热"},
    {"清洗"},
    {"复位"},
};

static bool boot_page_load_images(boot_page_state_t *state)
{
    return ep_platform_lvgl_image_src(BOOT_PAGE_LOGO_IMAGE_NAME,
                                      state->logo_src,
                                      sizeof(state->logo_src)) == EP_OK &&
           ep_platform_lvgl_image_src(BOOT_PAGE_SPINNER_IMAGE_NAME,
                                      state->spinner_src,
                                      sizeof(state->spinner_src)) == EP_OK &&
           ep_platform_lvgl_image_src(BOOT_PAGE_DONE_IMAGE_NAME,
                                      state->done_src,
                                      sizeof(state->done_src)) == EP_OK;
}

static void boot_page_delete_timer(boot_page_state_t *state)
{
    if (state != NULL && state->timer != NULL) {
        lv_timer_del(state->timer);
        state->timer = NULL;
    }
}

static void boot_page_delete_spinner_timer(boot_page_state_t *state)
{
    if (state != NULL && state->spinner_timer != NULL) {
        lv_timer_del(state->spinner_timer);
        state->spinner_timer = NULL;
    }
}

static bool boot_page_create_logo(boot_page_state_t *state)
{
    lv_obj_t *logo;

    logo = lv_image_create(state->screen);
    if (logo == NULL) {
        return false;
    }

    state->logo = logo;
    lv_obj_remove_style_all(logo);
    lv_obj_set_pos(logo, BOOT_PAGE_LOGO_X, BOOT_PAGE_LOGO_Y);
    lv_image_set_src(logo, state->logo_src);

    return true;
}

static lv_obj_t *boot_page_create_label(lv_obj_t *parent, const char *text)
{
    lv_obj_t *label_container;
    lv_obj_t *label;

    label_container = lv_obj_create(parent);
    if (label_container == NULL) {
        return NULL;
    }

    lv_obj_remove_style_all(label_container);
    lv_obj_set_size(label_container,
                    BOOT_PAGE_STAGE_TEXT_CONTAINER_WIDTH,
                    BOOT_PAGE_STAGE_TEXT_CONTAINER_HEIGHT);
    lv_obj_set_pos(label_container, BOOT_PAGE_STAGE_TEXT_CONTAINER_X, BOOT_PAGE_STAGE_TEXT_CONTAINER_Y);
    lv_obj_clear_flag(label_container, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLLABLE);

    label = lv_label_create(label_container);
    if (label == NULL) {
        return NULL;
    }

    lv_obj_remove_style_all(label);
    lv_obj_set_width(label, BOOT_PAGE_STAGE_TEXT_CONTAINER_WIDTH);
    lv_obj_set_height(label, LV_SIZE_CONTENT);
    lv_obj_set_style_text_color(label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(label, ui_style_font(UI_STYLE_FONT_HOME_USER), LV_PART_MAIN);
    lv_obj_set_style_text_align(label, LV_TEXT_ALIGN_CENTER, LV_PART_MAIN);
    lv_label_set_long_mode(label, LV_LABEL_LONG_CLIP);
    lv_label_set_text(label, text);
    lv_obj_center(label);

    return label_container;
}

static bool boot_page_create_stage_card(boot_page_state_t *state, size_t stage_index)
{
    lv_obj_t *card;
    lv_obj_t *icon_holder;
    lv_obj_t *icon;
    int32_t x;

    x = BOOT_PAGE_STAGE_FIRST_X +
        (int32_t)stage_index * (BOOT_PAGE_STAGE_CARD_WIDTH + BOOT_PAGE_STAGE_GAP);

    card = lv_obj_create(state->screen);
    if (card == NULL) {
        return false;
    }

    state->stage_cards[stage_index] = card;
    lv_obj_remove_style_all(card);
    lv_obj_set_size(card, BOOT_PAGE_STAGE_CARD_WIDTH, BOOT_PAGE_STAGE_CARD_HEIGHT);
    lv_obj_set_pos(card, x, BOOT_PAGE_STAGE_CARD_Y);
    lv_obj_set_style_bg_color(card, lv_color_hex(SETTINGS_PAGE_BUTTON_COLOR), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(card, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_radius(card, BOOT_PAGE_STAGE_CARD_RADIUS, LV_PART_MAIN);
    lv_obj_set_style_border_color(card, lv_color_hex(BOOT_PAGE_STAGE_BORDER_COLOR), LV_PART_MAIN);
    lv_obj_set_style_border_width(card, BOOT_PAGE_STAGE_CARD_BORDER_WIDTH, LV_PART_MAIN);
    lv_obj_set_style_border_opa(card, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_clear_flag(card, LV_OBJ_FLAG_SCROLLABLE);

    icon_holder = lv_obj_create(card);
    if (icon_holder == NULL) {
        return false;
    }

    state->stage_icon_holders[stage_index] = icon_holder;
    lv_obj_remove_style_all(icon_holder);
    lv_obj_set_size(icon_holder, BOOT_PAGE_STAGE_ICON_SIZE, BOOT_PAGE_STAGE_ICON_SIZE);
    lv_obj_set_pos(icon_holder, BOOT_PAGE_STAGE_ICON_X, BOOT_PAGE_STAGE_ICON_Y);
    lv_obj_clear_flag(icon_holder, LV_OBJ_FLAG_CLICKABLE | LV_OBJ_FLAG_SCROLLABLE);

    icon = lv_image_create(icon_holder);
    if (icon == NULL) {
        return false;
    }

    state->stage_icons[stage_index] = icon;
    lv_obj_remove_style_all(icon);
    lv_obj_set_size(icon, BOOT_PAGE_STAGE_ICON_SIZE, BOOT_PAGE_STAGE_ICON_SIZE);
    lv_image_set_pivot(icon, BOOT_PAGE_STAGE_ICON_SIZE / 2, BOOT_PAGE_STAGE_ICON_SIZE / 2);
    lv_image_set_src(icon, stage_index == 0u ? state->spinner_src : state->spinner_src);
    lv_obj_center(icon);
    lv_obj_add_flag(icon, LV_OBJ_FLAG_HIDDEN);

    if (boot_page_create_label(card, boot_page_stages[stage_index].label) == NULL) {
        return false;
    }

    return true;
}

static bool boot_page_create_stage_view(boot_page_state_t *state)
{
    lv_obj_add_flag(state->logo, LV_OBJ_FLAG_HIDDEN);

    for (size_t i = 0u; i < BOOT_PAGE_STAGE_COUNT; ++i) {
        if (!boot_page_create_stage_card(state, i)) {
            return false;
        }
    }

    state->active_stage = 0u;
    state->spinner_rotation = 0;
    lv_obj_clear_flag(state->stage_icons[state->active_stage], LV_OBJ_FLAG_HIDDEN);
    lv_timer_set_period(state->timer, BOOT_PAGE_STAGE_DELAY_MS);
    lv_timer_reset(state->timer);

    return true;
}

static void boot_page_finish_stage(boot_page_state_t *state, size_t stage_index)
{
    if (stage_index >= BOOT_PAGE_STAGE_COUNT || state->stage_icons[stage_index] == NULL) {
        return;
    }

    lv_image_set_rotation(state->stage_icons[stage_index], 0);
    lv_image_set_src(state->stage_icons[stage_index], state->done_src);
    lv_obj_clear_flag(state->stage_icons[stage_index], LV_OBJ_FLAG_HIDDEN);
}

static void boot_page_spinner_timer_cb(lv_timer_t *timer)
{
    boot_page_state_t *state;

    state = (boot_page_state_t *)lv_timer_get_user_data(timer);
    if (state == NULL ||
        state->phase != BOOT_PAGE_PHASE_STAGES ||
        state->active_stage >= BOOT_PAGE_STAGE_COUNT ||
        state->stage_icons[state->active_stage] == NULL) {
        return;
    }

    state->spinner_rotation = (state->spinner_rotation + BOOT_PAGE_SPINNER_STEP_DEG) % 3600;
    lv_image_set_rotation(state->stage_icons[state->active_stage], state->spinner_rotation);
}

static void boot_page_timer_cb(lv_timer_t *timer)
{
    boot_page_state_t *state;

    state = (boot_page_state_t *)lv_timer_get_user_data(timer);
    if (state == NULL) {
        return;
    }

    if (state->phase == BOOT_PAGE_PHASE_LOGO) {
        state->phase = BOOT_PAGE_PHASE_STAGES;
        (void)boot_page_create_stage_view(state);
        state->spinner_timer = lv_timer_create(boot_page_spinner_timer_cb, BOOT_PAGE_SPINNER_PERIOD_MS, state);
        return;
    }

    if (state->active_stage < BOOT_PAGE_STAGE_COUNT) {
        boot_page_finish_stage(state, state->active_stage);
        state->active_stage++;
    }

    if (state->active_stage >= BOOT_PAGE_STAGE_COUNT) {
        boot_page_delete_spinner_timer(state);
        boot_page_delete_timer(state);
        (void)page_manager_switch(APP_PAGE_HOME, LV_SCR_LOAD_ANIM_NONE, 0, false);
        return;
    }

    lv_image_set_src(state->stage_icons[state->active_stage], state->spinner_src);
    lv_obj_clear_flag(state->stage_icons[state->active_stage], LV_OBJ_FLAG_HIDDEN);
    state->spinner_rotation = 0;
    lv_image_set_rotation(state->stage_icons[state->active_stage], state->spinner_rotation);
    lv_timer_reset(state->timer);
}

lv_obj_t *boot_page_create(page_manager_page_ctx_t *ctx)
{
    boot_page_state_t *state;
    lv_obj_t *screen;

    (void)ctx;

    state = (boot_page_state_t *)calloc(1u, sizeof(*state));
    if (state == NULL) {
        return NULL;
    }

    screen = lv_obj_create(NULL);
    if (screen == NULL) {
        free(state);
        return NULL;
    }

    state->screen = screen;
    state->phase = BOOT_PAGE_PHASE_LOGO;
    lv_obj_set_user_data(screen, state);
    (void)ui_style_init();
    settings_common_style_screen(screen);

    if (!boot_page_load_images(state) ||
        !boot_page_create_logo(state)) {
        lv_obj_delete(screen);
        free(state);
        return NULL;
    }

    state->timer = lv_timer_create(boot_page_timer_cb, BOOT_PAGE_LOGO_DELAY_MS, state);
    if (state->timer == NULL) {
        lv_obj_delete(screen);
        free(state);
        return NULL;
    }

    return screen;
}

void boot_page_destroy(page_manager_page_ctx_t *ctx)
{
    boot_page_state_t *state;

    if (ctx == NULL || ctx->screen == NULL) {
        return;
    }

    state = (boot_page_state_t *)lv_obj_get_user_data(ctx->screen);
    boot_page_delete_spinner_timer(state);
    boot_page_delete_timer(state);
    free(state);
}

void boot_page_event(page_manager_page_ctx_t *ctx, uint32_t code, uint32_t wparam, uint32_t lparam)
{
    (void)ctx;
    (void)code;
    (void)wparam;
    (void)lparam;
}
