#include "ep_platform_capability.h"

static const char *const g_ep_platform_capability_names[EP_PLATFORM_CAPABILITY_COUNT] = {
    "filesystem",
    "config_persistence",
    "log",
    "thread",
    "lvgl",
    "display",
    "touch",
    "gpio",
    "i2c",
    "spi",
    "uart",
    "pwm",
    "adc",
    "rtc",
    "network",
};

static const unsigned char g_ep_host_platform_capabilities[EP_PLATFORM_CAPABILITY_COUNT] = {
    1u, /* filesystem */
    1u, /* config_persistence */
    1u, /* log */
    1u, /* thread */
#if defined(EP_HAS_HOST_SDL2_UI) && EP_HAS_HOST_SDL2_UI
    1u, /* lvgl */
    1u, /* display */
    1u, /* touch */
#else
    0u, /* lvgl */
    0u, /* display */
    0u, /* touch */
#endif
    0u, /* gpio */
    0u, /* i2c */
    0u, /* spi */
    0u, /* uart */
    0u, /* pwm */
    0u, /* adc */
    0u, /* rtc */
    0u, /* network */
};

int ep_platform_has_capability(ep_platform_capability_e capability)
{
    if (capability < 0 || capability >= EP_PLATFORM_CAPABILITY_COUNT) {
        return 0;
    }

    return g_ep_host_platform_capabilities[capability] != 0u;
}

const char *ep_platform_capability_name(ep_platform_capability_e capability)
{
    if (capability < 0 || capability >= EP_PLATFORM_CAPABILITY_COUNT) {
        return "unknown";
    }

    return g_ep_platform_capability_names[capability];
}
