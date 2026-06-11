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
        *out_text = key;
        return EP_ERR_INVAL;
    }

    *out_text = text_item->valuestring;
    return EP_OK;
}
