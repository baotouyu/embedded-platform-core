#include "app_ui.h"

#include "ep_log.h"
#include "page_manager.h"
#include "pages/app_pages.h"
#include "pages/home_page.h"
#include "pages/settings_page.h"

int app_ui_create(void)
{
    int rc;

    rc = page_manager_init(NULL);
    if (rc != 0) {
        return rc;
    }

    rc = page_manager_register(APP_PAGE_HOME, home_page_create, home_page_event, home_page_destroy);
    if (rc != 0) {
        return rc;
    }

    rc = page_manager_register(APP_PAGE_SETTINGS, settings_page_create, settings_page_event, NULL);
    if (rc != 0) {
        return rc;
    }

    rc = page_manager_switch(APP_PAGE_HOME, LV_SCR_LOAD_ANIM_NONE, 0, false);
    if (rc != 0) {
        return rc;
    }

    EP_LOGI("app", "app ui ready");

    return rc;
}
