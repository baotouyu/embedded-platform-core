#include "ep_simple_recipe.h"

#include "cJSON.h"
#include "ep_osal_err.h"
#include "sqlite3.h"

#include <stdlib.h>
#include <string.h>

struct ep_simple_recipe_store {
    sqlite3 *db;
};

static int ep_simple_recipe_copy_string(char *dst, size_t dst_size, const char *src)
{
    size_t len;

    if (dst == 0 || dst_size == 0u || src == 0) {
        return EP_ERR_INVAL;
    }

    len = strlen(src);
    if (len >= dst_size) {
        dst[0] = '\0';
        return EP_ERR_INVAL;
    }

    (void)memcpy(dst, src, len + 1u);
    return EP_OK;
}

static const char *ep_simple_recipe_json_string(cJSON *root, const char *key)
{
    cJSON *item;

    item = cJSON_GetObjectItemCaseSensitive(root, key);
    if (!cJSON_IsString(item) || item->valuestring == 0) {
        return "";
    }

    return item->valuestring;
}

static int ep_simple_recipe_fill_item_from_tabular_json(
    ep_simple_recipe_item_t *item,
    const char *tabular_json)
{
    cJSON *root;
    const char *portrait_url;
    const char *landscape_url;

    if (item == 0 || tabular_json == 0) {
        return EP_ERR_INVAL;
    }

    root = cJSON_Parse(tabular_json);
    if (root == 0) {
        return EP_ERR_INVAL;
    }

    portrait_url = ep_simple_recipe_json_string(root, "portraitImageUrl");
    landscape_url = ep_simple_recipe_json_string(root, "landscapeImageUrl");

    if (ep_simple_recipe_copy_string(item->portrait_image_url, sizeof(item->portrait_image_url), portrait_url) != EP_OK ||
        ep_simple_recipe_copy_string(item->landscape_image_url, sizeof(item->landscape_image_url), landscape_url) != EP_OK) {
        cJSON_Delete(root);
        return EP_ERR_INVAL;
    }

    cJSON_Delete(root);
    return EP_OK;
}

static int ep_simple_recipe_fill_item_from_statement(
    sqlite3_stmt *stmt,
    ep_simple_recipe_item_t *item)
{
    const unsigned char *recipe_id;
    const unsigned char *name;
    const unsigned char *tabular_detail;

    if (stmt == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    (void)memset(item, 0, sizeof(*item));

    recipe_id = sqlite3_column_text(stmt, 0);
    name = sqlite3_column_text(stmt, 1);
    tabular_detail = sqlite3_column_text(stmt, 2);

    if (recipe_id == 0 || name == 0 || tabular_detail == 0) {
        return EP_ERR_INVAL;
    }

    if (ep_simple_recipe_copy_string(item->id, sizeof(item->id), (const char *)recipe_id) != EP_OK ||
        ep_simple_recipe_copy_string(item->name, sizeof(item->name), (const char *)name) != EP_OK) {
        return EP_ERR_INVAL;
    }

    return ep_simple_recipe_fill_item_from_tabular_json(item, (const char *)tabular_detail);
}

static void ep_simple_recipe_fill_param_value(
    cJSON *param_value,
    ep_simple_recipe_param_t *param)
{
    const char *value;

    value = ep_simple_recipe_json_string(param_value, "ctlVal");
    (void)ep_simple_recipe_copy_string(param->ctl_val, sizeof(param->ctl_val), value);

    value = ep_simple_recipe_json_string(param_value, "minVal");
    (void)ep_simple_recipe_copy_string(param->min_val, sizeof(param->min_val), value);

    value = ep_simple_recipe_json_string(param_value, "maxVal");
    (void)ep_simple_recipe_copy_string(param->max_val, sizeof(param->max_val), value);

    value = ep_simple_recipe_json_string(param_value, "rangeVal");
    (void)ep_simple_recipe_copy_string(param->range_val, sizeof(param->range_val), value);
}

static int ep_simple_recipe_parse_step_params(cJSON *step_json, ep_simple_recipe_step_t *step)
{
    cJSON *params;
    cJSON *param_wrapper;

    params = cJSON_GetObjectItemCaseSensitive(step_json, "recipeStepParameterVoList");
    if (!cJSON_IsArray(params)) {
        return EP_OK;
    }

    cJSON_ArrayForEach(param_wrapper, params) {
        cJSON *param_value;
        ep_simple_recipe_param_t *param;

        if (step->param_count >= EP_SIMPLE_RECIPE_MAX_PARAMS_PER_STEP) {
            return EP_ERR_BUSY;
        }

        if (!cJSON_IsObject(param_wrapper) || param_wrapper->child == 0) {
            continue;
        }

        param_value = param_wrapper->child;
        if (!cJSON_IsObject(param_value) || param_value->string == 0) {
            continue;
        }

        param = &step->params[step->param_count];
        (void)memset(param, 0, sizeof(*param));
        if (ep_simple_recipe_copy_string(param->key, sizeof(param->key), param_value->string) != EP_OK) {
            return EP_ERR_INVAL;
        }
        ep_simple_recipe_fill_param_value(param_value, param);
        step->param_count++;
    }

    return EP_OK;
}

static int ep_simple_recipe_parse_steps(cJSON *root, ep_simple_recipe_detail_t *detail)
{
    cJSON *steps;
    cJSON *step_json;

    steps = cJSON_GetObjectItemCaseSensitive(root, "recipeStepVoList");
    if (!cJSON_IsArray(steps)) {
        return EP_OK;
    }

    cJSON_ArrayForEach(step_json, steps) {
        ep_simple_recipe_step_t *step;
        int rc;

        if (detail->step_count >= EP_SIMPLE_RECIPE_MAX_STEPS) {
            return EP_ERR_BUSY;
        }

        if (!cJSON_IsObject(step_json)) {
            continue;
        }

        step = &detail->steps[detail->step_count];
        (void)memset(step, 0, sizeof(*step));
        rc = ep_simple_recipe_parse_step_params(step_json, step);
        if (rc != EP_OK) {
            return rc;
        }

        detail->step_count++;
    }

    return EP_OK;
}

static int ep_simple_recipe_fill_detail_from_json(
    ep_simple_recipe_detail_t *detail,
    const char *recipe_detail_json)
{
    cJSON *root;
    int rc;

    root = cJSON_Parse(recipe_detail_json);
    if (root == 0) {
        return EP_ERR_INVAL;
    }

    rc = ep_simple_recipe_parse_steps(root, detail);
    cJSON_Delete(root);
    return rc;
}

int ep_simple_recipe_open_saas2_db(
    const char *db_path,
    ep_simple_recipe_store_t **out_store)
{
    ep_simple_recipe_store_t *store;
    int rc;

    if (db_path == 0 || db_path[0] == '\0' || out_store == 0) {
        return EP_ERR_INVAL;
    }

    *out_store = 0;

    store = (ep_simple_recipe_store_t *)calloc(1u, sizeof(*store));
    if (store == 0) {
        return EP_ERR_BUSY;
    }

    rc = sqlite3_open_v2(db_path, &store->db, SQLITE_OPEN_READONLY, 0);
    if (rc != SQLITE_OK) {
        ep_simple_recipe_close(store);
        return EP_ERR_INVAL;
    }

    *out_store = store;
    return EP_OK;
}

void ep_simple_recipe_close(ep_simple_recipe_store_t *store)
{
    if (store == 0) {
        return;
    }

    if (store->db != 0) {
        (void)sqlite3_close(store->db);
    }

    free(store);
}

int ep_simple_recipe_count(
    ep_simple_recipe_store_t *store,
    size_t *out_count)
{
    sqlite3_stmt *stmt = 0;
    int rc;

    if (store == 0 || store->db == 0 || out_count == 0) {
        return EP_ERR_INVAL;
    }

    *out_count = 0u;

    rc = sqlite3_prepare_v2(
        store->db,
        "select count(*) from SimpleRecipeEntity",
        -1,
        &stmt,
        0);
    if (rc != SQLITE_OK) {
        return EP_ERR_INVAL;
    }

    rc = sqlite3_step(stmt);
    if (rc == SQLITE_ROW) {
        *out_count = (size_t)sqlite3_column_int64(stmt, 0);
        rc = EP_OK;
    } else {
        rc = EP_ERR_INVAL;
    }

    (void)sqlite3_finalize(stmt);
    return rc;
}

int ep_simple_recipe_load_list(
    ep_simple_recipe_store_t *store,
    ep_simple_recipe_item_t *items,
    size_t capacity,
    size_t *out_count)
{
    sqlite3_stmt *stmt = 0;
    size_t loaded = 0u;
    int rc;

    if (store == 0 || store->db == 0 || out_count == 0 || (items == 0 && capacity > 0u)) {
        return EP_ERR_INVAL;
    }

    *out_count = 0u;

    rc = sqlite3_prepare_v2(
        store->db,
        "select recipeId, name, tabularDetail "
        "from SimpleRecipeEntity "
        "order by sort asc, id asc",
        -1,
        &stmt,
        0);
    if (rc != SQLITE_OK) {
        return EP_ERR_INVAL;
    }

    while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
        if (loaded >= capacity) {
            (void)sqlite3_finalize(stmt);
            return EP_ERR_BUSY;
        }

        rc = ep_simple_recipe_fill_item_from_statement(stmt, &items[loaded]);
        if (rc != EP_OK) {
            (void)sqlite3_finalize(stmt);
            return rc;
        }

        loaded++;
    }

    if (rc != SQLITE_DONE) {
        (void)sqlite3_finalize(stmt);
        return EP_ERR_INVAL;
    }

    (void)sqlite3_finalize(stmt);
    *out_count = loaded;
    return EP_OK;
}

int ep_simple_recipe_load_detail(
    ep_simple_recipe_store_t *store,
    const char *id,
    ep_simple_recipe_detail_t *out_detail)
{
    sqlite3_stmt *stmt = 0;
    const unsigned char *recipe_detail;
    int rc;

    if (store == 0 || store->db == 0 || id == 0 || id[0] == '\0' || out_detail == 0) {
        return EP_ERR_INVAL;
    }

    (void)memset(out_detail, 0, sizeof(*out_detail));

    rc = sqlite3_prepare_v2(
        store->db,
        "select recipeDetail "
        "from SimpleRecipeEntity "
        "where recipeId = ?",
        -1,
        &stmt,
        0);
    if (rc != SQLITE_OK) {
        return EP_ERR_INVAL;
    }

    rc = sqlite3_bind_text(stmt, 1, id, -1, SQLITE_TRANSIENT);
    if (rc != SQLITE_OK) {
        (void)sqlite3_finalize(stmt);
        return EP_ERR_INVAL;
    }

    rc = sqlite3_step(stmt);
    if (rc != SQLITE_ROW) {
        (void)sqlite3_finalize(stmt);
        return rc == SQLITE_DONE ? EP_ERR_INVAL : EP_ERR_BUSY;
    }

    recipe_detail = sqlite3_column_text(stmt, 0);
    if (recipe_detail == 0) {
        (void)sqlite3_finalize(stmt);
        return EP_ERR_INVAL;
    }

    rc = ep_simple_recipe_fill_detail_from_json(out_detail, (const char *)recipe_detail);
    (void)sqlite3_finalize(stmt);
    return rc;
}
