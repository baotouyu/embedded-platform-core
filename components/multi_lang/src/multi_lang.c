#include "multi_lang.h"

#include "cJSON.h"
#include "ep_osal_err.h"
#include "sqlite3.h"

#include <stdlib.h>
#include <string.h>

struct multi_lang_store {
    sqlite3 *db;
    cJSON *language_json;
    char *language;
};

typedef struct {
    const char *language;
    const char *key;
    const char *text;
} multi_lang_builtin_fallback_t;

static const multi_lang_builtin_fallback_t multi_lang_builtin_fallbacks[] = {
    {"en", MULTI_LANG_KEY_SETTING, "Settings"},
    {"en", MULTI_LANG_KEY_LANGUAGE, "Language"},
    {"en", MULTI_LANG_KEY_WIFI, "Wi-Fi"},
    {"en", MULTI_LANG_KEY_BRIGHTNESS, "Brightness"},
    {"en", MULTI_LANG_KEY_ON, "On"},
    {"en", MULTI_LANG_KEY_RINSE, "Clean"},
    {"en", MULTI_LANG_KEY_SLEEP, "Sleep"},
    {"en", MULTI_LANG_KEY_APP_LINK, "App Link"},
    {"en", MULTI_LANG_KEY_DETAILS, "Details"},
    {"zh-CN", MULTI_LANG_KEY_SETTING, "设置"},
    {"zh-CN", MULTI_LANG_KEY_LANGUAGE, "语言"},
    {"zh-CN", MULTI_LANG_KEY_WIFI, "Wi-Fi"},
    {"zh-CN", MULTI_LANG_KEY_BRIGHTNESS, "亮度"},
    {"zh-CN", MULTI_LANG_KEY_ON, "开"},
    {"zh-CN", MULTI_LANG_KEY_RINSE, "清洗"},
    {"zh-CN", MULTI_LANG_KEY_SLEEP, "休眠"},
    {"zh-CN", MULTI_LANG_KEY_APP_LINK, "App关联"},
    {"zh-CN", MULTI_LANG_KEY_DETAILS, "详细信息"},
};

static const char *multi_lang_get_builtin_text(const char *language, const char *key)
{
    size_t fallback_count;

    if (language == 0 || key == 0) {
        return 0;
    }

    fallback_count = sizeof(multi_lang_builtin_fallbacks) / sizeof(multi_lang_builtin_fallbacks[0]);
    for (size_t i = 0; i < fallback_count; ++i) {
        if (strcmp(multi_lang_builtin_fallbacks[i].language, language) == 0 &&
            strcmp(multi_lang_builtin_fallbacks[i].key, key) == 0) {
            return multi_lang_builtin_fallbacks[i].text;
        }
    }

    if (strcmp(language, MULTI_LANG_DEFAULT) != 0) {
        return multi_lang_get_builtin_text(MULTI_LANG_DEFAULT, key);
    }

    return 0;
}

static void multi_lang_clear_cache(multi_lang_store_t *store)
{
    if (store == 0) {
        return;
    }

    if (store->language_json != 0) {
        cJSON_Delete(store->language_json);
        store->language_json = 0;
    }

    free(store->language);
    store->language = 0;
}

static char *multi_lang_duplicate_string(const char *value)
{
    size_t len;
    char *copy;

    if (value == 0) {
        return 0;
    }

    len = strlen(value);
    copy = (char *)malloc(len + 1u);
    if (copy == 0) {
        return 0;
    }

    (void)memcpy(copy, value, len + 1u);
    return copy;
}

int multi_lang_open_db(const char *db_path, multi_lang_store_t **out_store)
{
    multi_lang_store_t *store;
    int rc;

    if (db_path == 0 || db_path[0] == '\0' || out_store == 0) {
        return EP_ERR_INVAL;
    }

    *out_store = 0;

    store = (multi_lang_store_t *)calloc(1u, sizeof(*store));
    if (store == 0) {
        return EP_ERR_BUSY;
    }

    rc = sqlite3_open_v2(db_path, &store->db, SQLITE_OPEN_READONLY, 0);
    if (rc != SQLITE_OK) {
        multi_lang_close(store);
        return EP_ERR_INVAL;
    }

    *out_store = store;
    return EP_OK;
}

void multi_lang_close(multi_lang_store_t *store)
{
    if (store == 0) {
        return;
    }

    multi_lang_clear_cache(store);

    if (store->db != 0) {
        (void)sqlite3_close(store->db);
    }

    free(store);
}

int multi_lang_set_language(multi_lang_store_t *store, const char *lang)
{
    sqlite3_stmt *stmt = 0;
    const unsigned char *content;
    cJSON *language_json;
    char *language;
    int rc;

    if (store == 0 || store->db == 0 || lang == 0 || lang[0] == '\0') {
        return EP_ERR_INVAL;
    }

    if (store->language != 0 &&
        strcmp(store->language, lang) == 0 &&
        store->language_json != 0) {
        return EP_OK;
    }

    rc = sqlite3_prepare_v2(
        store->db,
        "select content from \"interface\" where language = ?",
        -1,
        &stmt,
        0);
    if (rc != SQLITE_OK) {
        return EP_ERR_INVAL;
    }

    rc = sqlite3_bind_text(stmt, 1, lang, -1, SQLITE_TRANSIENT);
    if (rc != SQLITE_OK) {
        (void)sqlite3_finalize(stmt);
        return EP_ERR_INVAL;
    }

    rc = sqlite3_step(stmt);
    if (rc != SQLITE_ROW) {
        (void)sqlite3_finalize(stmt);
        return rc == SQLITE_DONE ? EP_ERR_INVAL : EP_ERR_BUSY;
    }

    content = sqlite3_column_text(stmt, 0);
    if (content == 0) {
        (void)sqlite3_finalize(stmt);
        return EP_ERR_INVAL;
    }

    language_json = cJSON_Parse((const char *)content);
    if (language_json == 0) {
        (void)sqlite3_finalize(stmt);
        return EP_ERR_INVAL;
    }

    language = multi_lang_duplicate_string(lang);
    if (language == 0) {
        cJSON_Delete(language_json);
        (void)sqlite3_finalize(stmt);
        return EP_ERR_BUSY;
    }

    multi_lang_clear_cache(store);
    store->language_json = language_json;
    store->language = language;

    (void)sqlite3_finalize(stmt);
    return EP_OK;
}

int multi_lang_get_text(
    multi_lang_store_t *store,
    const char *key,
    const char **out_text)
{
    cJSON *text_item;

    if (out_text != 0) {
        *out_text = key;
    }

    if (store == 0 || key == 0 || key[0] == '\0' || out_text == 0) {
        return EP_ERR_INVAL;
    }

    if (store->language_json == 0) {
        return EP_ERR_INVAL;
    }

    text_item = cJSON_GetObjectItemCaseSensitive(store->language_json, key);
    if (!cJSON_IsString(text_item) || text_item->valuestring == 0) {
        const char *builtin_text = multi_lang_get_builtin_text(store->language, key);
        if (builtin_text != 0) {
            *out_text = builtin_text;
            return EP_OK;
        }

        *out_text = key;
        return EP_ERR_INVAL;
    }

    *out_text = text_item->valuestring;
    return EP_OK;
}
