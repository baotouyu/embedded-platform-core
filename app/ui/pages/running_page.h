#ifndef RUNNING_PAGE_H
#define RUNNING_PAGE_H

#include "ep_simple_recipe.h"
#include "page_manager.h"

#include <stdint.h>

void running_page_set_recipe_context(const ep_simple_recipe_item_t *recipe, const char *image_src);
lv_obj_t *running_page_create(page_manager_page_ctx_t *ctx);
void running_page_event(page_manager_page_ctx_t *ctx, uint32_t code, uint32_t wparam, uint32_t lparam);
void running_page_destroy(page_manager_page_ctx_t *ctx);

#endif
