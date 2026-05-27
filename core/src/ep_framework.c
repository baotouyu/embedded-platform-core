#include "ep_framework.h"
#include "app_main.h"

int ep_framework_init(void)
{
    return 0;
}

int ep_framework_start(void)
{
    int rc = ep_platform_boot();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_init();
    if (rc != 0) {
        return rc;
    }

    return app_main();
}
