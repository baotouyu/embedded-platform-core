#include "ep_config.h"
#include "ep_file.h"
#include "ep_osal_err.h"

#include <errno.h>
#include <limits.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#define EP_CONFIG_MAX_ITEMS 32u
#define EP_CONFIG_KEY_MAX_LEN 48u
#define EP_CONFIG_STRING_MAX_LEN 96u
#define EP_CONFIG_FILE_MAX_SIZE 1024u
#define EP_CONFIG_LINE_MAX_LEN 128u

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

static int ep_config_read_file(const char *path, char *buffer, size_t buffer_size, size_t *content_size)
{
    ep_file_t *file = 0;
    size_t total = 0u;
    int rc;

    if (content_size == 0 || buffer == 0 || buffer_size == 0u) {
        return EP_ERR_INVAL;
    }

    *content_size = 0u;

    rc = ep_file_open(&file, path, EP_FILE_MODE_READ);
    if (rc != EP_OK) {
        return rc;
    }

    while (total < buffer_size - 1u) {
        size_t bytes_read = 0u;

        rc = ep_file_read(file, buffer + total, (buffer_size - 1u) - total, &bytes_read);
        if (rc != EP_OK) {
            (void)ep_file_close(file);
            return rc;
        }

        if (bytes_read == 0u) {
            break;
        }

        total += bytes_read;
    }

    if (total == buffer_size - 1u) {
        size_t extra = 0u;

        rc = ep_file_read(file, buffer + total, 1u, &extra);
        if (rc != EP_OK) {
            (void)ep_file_close(file);
            return rc;
        }

        if (extra != 0u) {
            (void)ep_file_close(file);
            return EP_ERR_BUSY;
        }
    }

    rc = ep_file_close(file);
    if (rc != EP_OK) {
        return rc;
    }

    buffer[total] = '\0';
    *content_size = total;
    return EP_OK;
}

static int ep_config_parse_int_value(const char *value, int *out_value)
{
    char *end = 0;
    long parsed;

    if (value == 0 || value[0] == '\0' || out_value == 0) {
        return EP_ERR_INVAL;
    }

    errno = 0;
    parsed = strtol(value, &end, 10);
    if (errno != 0 || end == value || end == 0 || end[0] != '\0') {
        return EP_ERR_INVAL;
    }

    if (parsed < INT_MIN || parsed > INT_MAX) {
        return EP_ERR_INVAL;
    }

    *out_value = (int)parsed;
    return EP_OK;
}

static int ep_config_parse_line(char *line)
{
    char *key;
    char *value;
    char *separator;
    int parsed_int;

    if (line == 0 || line[0] == '\0') {
        return EP_ERR_INVAL;
    }

    separator = strchr(line, '=');
    if (separator == 0) {
        return EP_ERR_INVAL;
    }

    *separator = '\0';
    value = separator + 1;
    if (value[0] == '\0') {
        return EP_ERR_INVAL;
    }

    if (strncmp(line, "int ", 4u) == 0) {
        key = line + 4;
        if (ep_config_parse_int_value(value, &parsed_int) != EP_OK) {
            return EP_ERR_INVAL;
        }
        return ep_config_set_int(key, parsed_int);
    }

    if (strncmp(line, "bool ", 5u) == 0) {
        key = line + 5;
        if (strcmp(value, "true") == 0) {
            return ep_config_set_bool(key, 1);
        }
        if (strcmp(value, "false") == 0) {
            return ep_config_set_bool(key, 0);
        }
        return EP_ERR_INVAL;
    }

    if (strncmp(line, "string ", 7u) == 0) {
        key = line + 7;
        return ep_config_set_string(key, value);
    }

    return EP_ERR_INVAL;
}

static int ep_config_parse_content(char *content)
{
    char *line = content;

    while (line != 0 && line[0] != '\0') {
        char *next = strchr(line, '\n');
        size_t line_len;
        int rc;

        if (next != 0) {
            *next = '\0';
        }

        line_len = strlen(line);
        if (line_len > 0u && line[line_len - 1u] == '\r') {
            line[line_len - 1u] = '\0';
            --line_len;
        }

        if (line_len >= EP_CONFIG_LINE_MAX_LEN) {
            return EP_ERR_INVAL;
        }

        rc = ep_config_parse_line(line);
        if (rc != EP_OK) {
            return rc;
        }

        if (next == 0) {
            break;
        }

        line = next + 1;
    }

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

int ep_config_load_file(const char *path)
{
    char content[EP_CONFIG_FILE_MAX_SIZE];
    size_t content_size = 0u;
    int rc;

    if (g_ep_config_initialized == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    if (path == 0 || path[0] == '\0') {
        return EP_ERR_INVAL;
    }

    rc = ep_config_read_file(path, content, sizeof(content), &content_size);
    if (rc != EP_OK) {
        return rc;
    }

    if (content_size == 0u) {
        return EP_ERR_INVAL;
    }

    return ep_config_parse_content(content);
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
