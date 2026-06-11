#ifndef HOME_PAGE_H
#define HOME_PAGE_H

#include "page_manager.h"

lv_obj_t *home_page_create(page_manager_page_ctx_t *ctx);
void home_page_destroy(page_manager_page_ctx_t *ctx);
void home_page_event(page_manager_page_ctx_t *ctx,
                     uint32_t code,
                     uint32_t wparam,
                     uint32_t lparam);

#endif
