#include "app_core.h"

#include "beep_service.h"
#include "ep_log.h"
#include "ep_osal_err.h"
#include "lcd_sleep_service.h"
#include "power_board_service.h"
#include "rtc_service.h"

void app_context_init(app_context_t *app)
{
    if (app == 0) {
        return;
    }

    app->services_ready = 0;
}

int app_core_start(app_context_t *app)
{
    int rc;

    if (app == 0) {
        return EP_ERR_INVAL;
    }

    EP_LOGI("app", "app lifecycle start");

    rc = beep_service_init();
    if (rc != EP_OK) {
        return rc;
    }

    rc = rtc_service_init();
    if (rc != EP_OK) {
        return rc;
    }

    rc = lcd_sleep_service_init();
    if (rc != EP_OK) {
        return rc;
    }

    rc = power_board_service_init();
    if (rc != EP_OK) {
        return rc;
    }

    app->services_ready = 1;
    return EP_OK;
}

int app_core_run(app_context_t *app)
{
    if (app == 0 || app->services_ready == 0) {
        return EP_ERR_INVAL;
    }

    EP_LOGI("app", "app lifecycle done");
    return EP_OK;
}
