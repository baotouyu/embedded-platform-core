#ifndef RUNNING_PAGE_H
#define RUNNING_PAGE_H

#include "page_manager.h"

#include <stdint.h>

lv_obj_t *running_page_create(page_manager_page_ctx_t *ctx);
void running_page_event(page_manager_page_ctx_t *ctx, uint32_t code, uint32_t wparam, uint32_t lparam);
void running_page_destroy(page_manager_page_ctx_t *ctx);

#endif
