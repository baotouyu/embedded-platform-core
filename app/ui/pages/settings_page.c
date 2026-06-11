#include "pages/settings_page.h"

#include "lvgl.h"
#include "pages/app_pages.h"

#define SETTINGS_PAGE_TITLE_TEXT "Settings"
#define SETTINGS_PAGE_BACK_TEXT "Back"
#define SETTINGS_PAGE_EVENT_REFRESH 1u

static void settings_page_back_clicked(lv_event_t *event)
{
    (void)event;
    (void)page_manager_back(LV_SCR_LOAD_ANIM_MOVE_RIGHT, 180);
}

lv_obj_t *settings_page_create(page_manager_page_ctx_t *ctx)
{
    lv_obj_t *screen;
    lv_obj_t *title;
    lv_obj_t *back_button;
    lv_obj_t *back_label;

    (void)ctx;

    screen = lv_obj_create(NULL);
    if (screen == NULL) {
        return NULL;
    }

    title = lv_label_create(screen);
    if (title == NULL) {
        lv_obj_delete(screen);
        return NULL;
    }

    back_button = lv_button_create(screen);
    if (back_button == NULL) {
        lv_obj_delete(screen);
        return NULL;
    }

    back_label = lv_label_create(back_button);
    if (back_label == NULL) {
        lv_obj_delete(screen);
        return NULL;
    }

    lv_label_set_text(title, SETTINGS_PAGE_TITLE_TEXT);
    lv_obj_align(title, LV_ALIGN_CENTER, 0, -28);

    lv_obj_set_size(back_button, 120, 40);
    lv_obj_align(back_button, LV_ALIGN_CENTER, 0, 36);
    lv_obj_add_event_cb(back_button, settings_page_back_clicked, LV_EVENT_CLICKED, NULL);

    lv_label_set_text(back_label, SETTINGS_PAGE_BACK_TEXT);
    lv_obj_center(back_label);

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
