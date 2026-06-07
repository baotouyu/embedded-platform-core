#include "app_ui.h"

#include "ep_log.h"
#include "ep_osal_err.h"
#include "lvgl.h"

#define APP_UI_TITLE_TEXT "embedded-platform-core"
#define APP_UI_STATUS_TEXT "Mac edit, target run"

int app_ui_create(void)
{
    lv_obj_t *screen = lv_screen_active();
    lv_obj_t *title;
    lv_obj_t *status;

    if (screen == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    title = lv_label_create(screen);
    if (title == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    status = lv_label_create(screen);
    if (status == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_label_set_text(title, APP_UI_TITLE_TEXT);
    lv_obj_align(title, LV_ALIGN_CENTER, 0, -18);

    lv_label_set_text(status, APP_UI_STATUS_TEXT);
    lv_obj_align(status, LV_ALIGN_CENTER, 0, 18);

    EP_LOGI("app", "app ui ready");

    return EP_OK;
}
