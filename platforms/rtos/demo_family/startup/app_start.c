#include "ep_framework.h"

int ep_platform_boot(void)
{
    return 0;
}

int vendor_app_start(void)
{
    return ep_framework_start();
}
