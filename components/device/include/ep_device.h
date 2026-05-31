#ifndef EP_DEVICE_H
#define EP_DEVICE_H

#include "ep_platform_capability.h"

typedef enum {
    EP_DEVICE_TYPE_GPIO = 0,
    EP_DEVICE_TYPE_I2C,
    EP_DEVICE_TYPE_SPI,
    EP_DEVICE_TYPE_UART,
    EP_DEVICE_TYPE_DISPLAY,
    EP_DEVICE_TYPE_TOUCH,
    EP_DEVICE_TYPE_STORAGE,
    EP_DEVICE_TYPE_NETWORK,
    EP_DEVICE_TYPE_SENSOR,
    EP_DEVICE_TYPE_OTHER,
    EP_DEVICE_TYPE_COUNT
} ep_device_type_e;

typedef enum {
    EP_DEVICE_STATE_OFFLINE = 0,
    EP_DEVICE_STATE_ONLINE,
    EP_DEVICE_STATE_ERROR,
    EP_DEVICE_STATE_COUNT
} ep_device_state_e;

typedef struct ep_device ep_device_t;

typedef struct {
    const char *name;
    ep_device_type_e type;
    ep_device_state_e state;
    ep_platform_capability_e capability;
    void *context;
} ep_device_desc_t;

int ep_device_init(void);
int ep_device_register(const ep_device_desc_t *desc, ep_device_t **device);
ep_device_t *ep_device_find(const char *name);
ep_device_t *ep_device_find_by_type(ep_device_type_e type, unsigned int index);

const char *ep_device_name(const ep_device_t *device);
ep_device_type_e ep_device_type(const ep_device_t *device);
ep_device_state_e ep_device_state(const ep_device_t *device);
ep_platform_capability_e ep_device_capability(const ep_device_t *device);
void *ep_device_context(const ep_device_t *device);

#endif
