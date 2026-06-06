#include "app_core.h"
#include "app_main.h"
#include "app_selftest.h"
#include "ep_osal_err.h"

int app_main(void)
{
    app_context_t app;
    int rc;

    app_context_init(&app);

    rc = app_core_start(&app);
    if (rc != EP_OK) {
        return rc;
    }

    rc = app_selftest_run(&app);
    if (rc != EP_OK) {
        return rc;
    }

    return app_core_run(&app);
}
