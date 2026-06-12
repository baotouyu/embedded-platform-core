#ifndef BOOT_PAGE_H
#define BOOT_PAGE_H

#include "page_manager.h"

lv_obj_t *boot_page_create(page_manager_page_ctx_t *ctx);
void boot_page_destroy(page_manager_page_ctx_t *ctx);
void boot_page_event(page_manager_page_ctx_t *ctx, uint32_t code, uint32_t wparam, uint32_t lparam);

#endif
