#include "ep_config.h"
#include "ep_osal_err.h"

#include <stddef.h>
#include <string.h>

#define EP_CONFIG_MAX_ITEMS 32u
#define EP_CONFIG_KEY_MAX_LEN 48u
#define EP_CONFIG_STRING_MAX_LEN 96u

typedef enum {
    EP_CONFIG_VALUE_INT = 0,
    EP_CONFIG_VALUE_BOOL = 1,
    EP_CONFIG_VALUE_STRING = 2
} ep_config_value_type_e;

typedef struct {
    int used;
    char key[EP_CONFIG_KEY_MAX_LEN];
    ep_config_value_type_e type;
    union {
        int int_value;
        int bool_value;
        char string_value[EP_CONFIG_STRING_MAX_LEN];
    } value;
} ep_config_entry_t;

static int g_ep_config_initialized;
static ep_config_entry_t g_ep_config_entries[EP_CONFIG_MAX_ITEMS];

static int ep_config_key_is_valid(const char *key)
{
    if (key == 0 || key[0] == '\0') {
        return 0;
    }

    return strlen(key) < EP_CONFIG_KEY_MAX_LEN;
}

static ep_config_entry_t *ep_config_find_entry(const char *key)
{
    size_t i;

    for (i = 0u; i < EP_CONFIG_MAX_ITEMS; ++i) {
        if (g_ep_config_entries[i].used != 0 &&
            strcmp(g_ep_config_entries[i].key, key) == 0) {
            return &g_ep_config_entries[i];
        }
    }

    return 0;
}

static ep_config_entry_t *ep_config_alloc_entry(void)
{
    size_t i;

    for (i = 0u; i < EP_CONFIG_MAX_ITEMS; ++i) {
        if (g_ep_config_entries[i].used == 0) {
            return &g_ep_config_entries[i];
        }
    }

    return 0;
}

static int ep_config_prepare_entry(const char *key, ep_config_entry_t **entry)
{
    ep_config_entry_t *found;

    if (entry == 0) {
        return EP_ERR_INVAL;
    }

    *entry = 0;

    if (g_ep_config_initialized == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    if (!ep_config_key_is_valid(key)) {
        return EP_ERR_INVAL;
    }

    found = ep_config_find_entry(key);
    if (found != 0) {
        *entry = found;
        return EP_OK;
    }

    found = ep_config_alloc_entry();
    if (found == 0) {
        return EP_ERR_BUSY;
    }

    found->used = 1;
    (void)strcpy(found->key, key);
    *entry = found;
    return EP_OK;
}

int ep_config_init(void)
{
    if (g_ep_config_initialized != 0) {
        return EP_OK;
    }

    (void)memset(g_ep_config_entries, 0, sizeof(g_ep_config_entries));
    g_ep_config_initialized = 1;
    return EP_OK;
}

int ep_config_set_int(const char *key, int value)
{
    ep_config_entry_t *entry;
    int rc = ep_config_prepare_entry(key, &entry);

    if (rc != EP_OK) {
        return rc;
    }

    entry->type = EP_CONFIG_VALUE_INT;
    entry->value.int_value = value;
    return EP_OK;
}

int ep_config_get_int(const char *key, int default_value)
{
    ep_config_entry_t *entry;

    if (g_ep_config_initialized == 0 || !ep_config_key_is_valid(key)) {
        return default_value;
    }

    entry = ep_config_find_entry(key);
    if (entry == 0 || entry->type != EP_CONFIG_VALUE_INT) {
        return default_value;
    }

    return entry->value.int_value;
}

int ep_config_set_bool(const char *key, int value)
{
    ep_config_entry_t *entry;
    int rc = ep_config_prepare_entry(key, &entry);

    if (rc != EP_OK) {
        return rc;
    }

    entry->type = EP_CONFIG_VALUE_BOOL;
    entry->value.bool_value = (value != 0) ? 1 : 0;
    return EP_OK;
}

int ep_config_get_bool(const char *key, int default_value)
{
    ep_config_entry_t *entry;

    if (g_ep_config_initialized == 0 || !ep_config_key_is_valid(key)) {
        return default_value;
    }

    entry = ep_config_find_entry(key);
    if (entry == 0 || entry->type != EP_CONFIG_VALUE_BOOL) {
        return default_value;
    }

    return entry->value.bool_value;
}

int ep_config_set_string(const char *key, const char *value)
{
    ep_config_entry_t *entry;
    int rc;

    if (value == 0 || strlen(value) >= EP_CONFIG_STRING_MAX_LEN) {
        return EP_ERR_INVAL;
    }

    rc = ep_config_prepare_entry(key, &entry);
    if (rc != EP_OK) {
        return rc;
    }

    entry->type = EP_CONFIG_VALUE_STRING;
    (void)strcpy(entry->value.string_value, value);
    return EP_OK;
}

const char *ep_config_get_string(const char *key, const char *default_value)
{
    ep_config_entry_t *entry;

    if (g_ep_config_initialized == 0 || !ep_config_key_is_valid(key)) {
        return default_value;
    }

    entry = ep_config_find_entry(key);
    if (entry == 0 || entry->type != EP_CONFIG_VALUE_STRING) {
        return default_value;
    }

    return entry->value.string_value;
}
