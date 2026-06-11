#ifndef SETTINGS_PAGE_H
#define SETTINGS_PAGE_H

#include "page_manager.h"

lv_obj_t *settings_page_create(page_manager_page_ctx_t *ctx);
void settings_page_event(page_manager_page_ctx_t *ctx,
                         uint32_t code,
                         uint32_t wparam,
                         uint32_t lparam);

#endif
