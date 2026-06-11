#ifndef PAGE_MANAGER_H
#define PAGE_MANAGER_H

#include <stdbool.h>
#include <stdint.h>

#include "lvgl.h"

typedef int32_t page_manager_page_id_t;

typedef struct {
    void *app_ctx;
    lv_obj_t *screen;
    page_manager_page_id_t page_id;
} page_manager_page_ctx_t;

typedef lv_obj_t *(*page_manager_create_cb_t)(page_manager_page_ctx_t *ctx);
typedef void (*page_manager_event_cb_t)(page_manager_page_ctx_t *ctx,
                                        uint32_t code,
                                        uint32_t wparam,
                                        uint32_t lparam);
typedef void (*page_manager_destroy_cb_t)(page_manager_page_ctx_t *ctx);

int page_manager_init(void *app_ctx);
int page_manager_register(page_manager_page_id_t page_id,
                          page_manager_create_cb_t create_cb,
                          page_manager_event_cb_t event_cb,
                          page_manager_destroy_cb_t destroy_cb);
int page_manager_switch(page_manager_page_id_t page_id,
                        lv_screen_load_anim_t anim_type,
                        uint32_t anim_time,
                        bool add_history);
int page_manager_back(lv_screen_load_anim_t anim_type, uint32_t anim_time);
int page_manager_send_event(page_manager_page_id_t page_id,
                            uint32_t code,
                            uint32_t wparam,
                            uint32_t lparam);
int page_manager_freeze(page_manager_page_id_t page_id);
int page_manager_unfreeze(page_manager_page_id_t page_id);
page_manager_page_id_t page_manager_current_page_id(void);

#endif
