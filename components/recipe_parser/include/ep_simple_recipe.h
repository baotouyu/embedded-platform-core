#ifndef EP_SIMPLE_RECIPE_H
#define EP_SIMPLE_RECIPE_H

#include <stddef.h>

#define EP_SIMPLE_RECIPE_ID_MAX_LEN 32u
#define EP_SIMPLE_RECIPE_NAME_MAX_LEN 128u
#define EP_SIMPLE_RECIPE_URL_MAX_LEN 256u
#define EP_SIMPLE_RECIPE_PARAM_KEY_MAX_LEN 48u
#define EP_SIMPLE_RECIPE_PARAM_VALUE_MAX_LEN 32u
#define EP_SIMPLE_RECIPE_PARAM_RANGE_MAX_LEN 64u
#define EP_SIMPLE_RECIPE_MAX_PARAMS_PER_STEP 16u
#define EP_SIMPLE_RECIPE_MAX_STEPS 8u

typedef struct ep_simple_recipe_store ep_simple_recipe_store_t;

typedef struct {
    char key[EP_SIMPLE_RECIPE_PARAM_KEY_MAX_LEN];
    char ctl_val[EP_SIMPLE_RECIPE_PARAM_VALUE_MAX_LEN];
    char min_val[EP_SIMPLE_RECIPE_PARAM_VALUE_MAX_LEN];
    char max_val[EP_SIMPLE_RECIPE_PARAM_VALUE_MAX_LEN];
    char range_val[EP_SIMPLE_RECIPE_PARAM_RANGE_MAX_LEN];
} ep_simple_recipe_param_t;

typedef struct {
    ep_simple_recipe_param_t params[EP_SIMPLE_RECIPE_MAX_PARAMS_PER_STEP];
    size_t param_count;
} ep_simple_recipe_step_t;

typedef struct {
    char id[EP_SIMPLE_RECIPE_ID_MAX_LEN];
    char name[EP_SIMPLE_RECIPE_NAME_MAX_LEN];
    char landscape_image_url[EP_SIMPLE_RECIPE_URL_MAX_LEN];
    char portrait_image_url[EP_SIMPLE_RECIPE_URL_MAX_LEN];
} ep_simple_recipe_item_t;

typedef struct {
    ep_simple_recipe_step_t steps[EP_SIMPLE_RECIPE_MAX_STEPS];
    size_t step_count;
} ep_simple_recipe_detail_t;

int ep_simple_recipe_open_saas2_db(
    const char *db_path,
    ep_simple_recipe_store_t **out_store);

void ep_simple_recipe_close(ep_simple_recipe_store_t *store);

int ep_simple_recipe_count(
    ep_simple_recipe_store_t *store,
    size_t *out_count);

int ep_simple_recipe_load_list(
    ep_simple_recipe_store_t *store,
    ep_simple_recipe_item_t *items,
    size_t capacity,
    size_t *out_count);

int ep_simple_recipe_load_detail(
    ep_simple_recipe_store_t *store,
    const char *id,
    ep_simple_recipe_detail_t *out_detail);

#endif
