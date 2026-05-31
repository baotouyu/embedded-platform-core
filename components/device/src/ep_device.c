#include "ep_device.h"
#include "ep_osal_err.h"

#include <stddef.h>
#include <string.h>

#define EP_DEVICE_MAX_DEVICES 8u
#define EP_DEVICE_NAME_MAX_LEN 32u

struct ep_device {
    int used;
    char name[EP_DEVICE_NAME_MAX_LEN];
    ep_device_type_e type;
    ep_device_state_e state;
    ep_platform_capability_e capability;
    void *context;
};

static int g_ep_device_initialized;
static ep_device_t g_ep_devices[EP_DEVICE_MAX_DEVICES];

static int ep_device_name_is_valid(const char *name)
{
    if (name == 0 || name[0] == '\0') {
        return 0;
    }

    return strlen(name) < EP_DEVICE_NAME_MAX_LEN;
}

static int ep_device_type_is_valid(ep_device_type_e type)
{
    return type >= EP_DEVICE_TYPE_GPIO && type < EP_DEVICE_TYPE_COUNT;
}

static int ep_device_state_is_valid(ep_device_state_e state)
{
    return state >= EP_DEVICE_STATE_OFFLINE && state < EP_DEVICE_STATE_COUNT;
}

static ep_device_t *ep_device_alloc_slot(void)
{
    size_t i;

    for (i = 0u; i < EP_DEVICE_MAX_DEVICES; ++i) {
        if (g_ep_devices[i].used == 0) {
            return &g_ep_devices[i];
        }
    }

    return 0;
}

int ep_device_init(void)
{
    g_ep_device_initialized = 1;
    return EP_OK;
}

int ep_device_register(const ep_device_desc_t *desc, ep_device_t **device)
{
    ep_device_t *slot;

    if (device != 0) {
        *device = 0;
    }

    if (g_ep_device_initialized == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    if (desc == 0 ||
        !ep_device_name_is_valid(desc->name) ||
        !ep_device_type_is_valid(desc->type) ||
        !ep_device_state_is_valid(desc->state)) {
        return EP_ERR_INVAL;
    }

    if (ep_device_find(desc->name) != 0) {
        return EP_ERR_BUSY;
    }

    slot = ep_device_alloc_slot();
    if (slot == 0) {
        return EP_ERR_BUSY;
    }

    slot->used = 1;
    (void)strcpy(slot->name, desc->name);
    slot->type = desc->type;
    slot->state = desc->state;
    slot->capability = desc->capability;
    slot->context = desc->context;

    if (device != 0) {
        *device = slot;
    }

    return EP_OK;
}

ep_device_t *ep_device_find(const char *name)
{
    size_t i;

    if (g_ep_device_initialized == 0 || !ep_device_name_is_valid(name)) {
        return 0;
    }

    for (i = 0u; i < EP_DEVICE_MAX_DEVICES; ++i) {
        if (g_ep_devices[i].used != 0 &&
            strcmp(g_ep_devices[i].name, name) == 0) {
            return &g_ep_devices[i];
        }
    }

    return 0;
}

ep_device_t *ep_device_find_by_type(ep_device_type_e type, unsigned int index)
{
    size_t i;
    unsigned int matched = 0u;

    if (g_ep_device_initialized == 0 || !ep_device_type_is_valid(type)) {
        return 0;
    }

    for (i = 0u; i < EP_DEVICE_MAX_DEVICES; ++i) {
        if (g_ep_devices[i].used != 0 && g_ep_devices[i].type == type) {
            if (matched == index) {
                return &g_ep_devices[i];
            }
            ++matched;
        }
    }

    return 0;
}

const char *ep_device_name(const ep_device_t *device)
{
    if (device == 0 || device->used == 0) {
        return 0;
    }

    return device->name;
}

ep_device_type_e ep_device_type(const ep_device_t *device)
{
    if (device == 0 || device->used == 0) {
        return EP_DEVICE_TYPE_COUNT;
    }

    return device->type;
}

ep_device_state_e ep_device_state(const ep_device_t *device)
{
    if (device == 0 || device->used == 0) {
        return EP_DEVICE_STATE_COUNT;
    }

    return device->state;
}

ep_platform_capability_e ep_device_capability(const ep_device_t *device)
{
    if (device == 0 || device->used == 0) {
        return EP_PLATFORM_CAPABILITY_COUNT;
    }

    return device->capability;
}

void *ep_device_context(const ep_device_t *device)
{
    if (device == 0 || device->used == 0) {
        return 0;
    }

    return device->context;
}
