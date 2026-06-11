#include "page_manager.h"

#include <stddef.h>

#include "ep_osal_err.h"

#define PAGE_MANAGER_MAX_PAGES 16
#define PAGE_MANAGER_HISTORY_SIZE 10
#define PAGE_MANAGER_NO_PAGE 0

typedef struct {
    bool in_use;
    bool is_frozen;
    page_manager_page_id_t page_id;
    lv_obj_t *screen;
    page_manager_create_cb_t create_cb;
    page_manager_event_cb_t event_cb;
    page_manager_destroy_cb_t destroy_cb;
} page_manager_entry_t;

static page_manager_entry_t page_entries[PAGE_MANAGER_MAX_PAGES];
static void *page_manager_app_ctx;
static page_manager_page_id_t current_page_id = PAGE_MANAGER_NO_PAGE;
static page_manager_page_id_t page_manager_transition_page_id = PAGE_MANAGER_NO_PAGE;
static page_manager_page_id_t page_history[PAGE_MANAGER_HISTORY_SIZE];
static size_t page_history_count;
static bool page_manager_initialized;
static bool page_manager_switching;

static page_manager_entry_t *page_manager_find(page_manager_page_id_t page_id)
{
    for (size_t i = 0; i < PAGE_MANAGER_MAX_PAGES; ++i) {
        if (page_entries[i].in_use && page_entries[i].page_id == page_id) {
            return &page_entries[i];
        }
    }

    return NULL;
}

static page_manager_entry_t *page_manager_find_free(void)
{
    for (size_t i = 0; i < PAGE_MANAGER_MAX_PAGES; ++i) {
        if (!page_entries[i].in_use) {
            return &page_entries[i];
        }
    }

    return NULL;
}

static void page_manager_screen_delete_event(lv_event_t *event)
{
    page_manager_entry_t *entry;
    lv_obj_t *target;

    if (lv_event_get_code(event) != LV_EVENT_DELETE) {
        return;
    }

    entry = (page_manager_entry_t *)lv_event_get_user_data(event);
    target = lv_event_get_current_target_obj(event);
    if (entry == NULL || entry->screen != target) {
        return;
    }

    if (entry->destroy_cb != NULL) {
        page_manager_page_ctx_t ctx = {
            .app_ctx = page_manager_app_ctx,
            .screen = entry->screen,
            .page_id = entry->page_id,
        };
        entry->destroy_cb(&ctx);
    }

    entry->screen = NULL;
}

static void page_manager_screen_loaded_event(lv_event_t *event)
{
    page_manager_entry_t *entry;
    lv_event_code_t code;

    code = lv_event_get_code(event);
    if (code != LV_EVENT_SCREEN_LOADED && code != LV_EVENT_SCREEN_UNLOADED) {
        return;
    }

    entry = (page_manager_entry_t *)lv_event_get_user_data(event);
    if (entry == NULL) {
        return;
    }

    if (code == LV_EVENT_SCREEN_LOADED && entry->page_id == page_manager_transition_page_id) {
        current_page_id = entry->page_id;
        page_manager_transition_page_id = PAGE_MANAGER_NO_PAGE;
        page_manager_switching = false;
    }
}

static void page_manager_clear_history(void)
{
    for (size_t i = 0; i < PAGE_MANAGER_HISTORY_SIZE; ++i) {
        page_history[i] = PAGE_MANAGER_NO_PAGE;
    }
    page_history_count = 0;
}

static void page_manager_push_history(page_manager_page_id_t page_id)
{
    if (page_id == PAGE_MANAGER_NO_PAGE) {
        return;
    }

    if (page_history_count == PAGE_MANAGER_HISTORY_SIZE) {
        for (size_t i = 1; i < PAGE_MANAGER_HISTORY_SIZE; ++i) {
            page_history[i - 1] = page_history[i];
        }
        page_history_count = PAGE_MANAGER_HISTORY_SIZE - 1;
    }

    page_history[page_history_count] = page_id;
    page_history_count++;
}

static int page_manager_load_page(page_manager_page_id_t page_id,
                                  lv_screen_load_anim_t anim_type,
                                  uint32_t anim_time,
                                  bool add_history)
{
    page_manager_entry_t *entry;
    lv_obj_t *screen;
    page_manager_page_ctx_t ctx;

    if (!page_manager_initialized || page_manager_switching) {
        return EP_ERR_UNSUPPORTED;
    }

    entry = page_manager_find(page_id);
    if (entry == NULL || entry->create_cb == NULL) {
        return EP_ERR_INVAL;
    }

    if (entry->is_frozen) {
        return EP_ERR_UNSUPPORTED;
    }

    if (entry->screen == NULL) {
        ctx.app_ctx = page_manager_app_ctx;
        ctx.screen = NULL;
        ctx.page_id = page_id;
        screen = entry->create_cb(&ctx);
        if (screen == NULL) {
            return EP_ERR_UNSUPPORTED;
        }

        entry->screen = screen;
        lv_obj_add_event_cb(entry->screen, page_manager_screen_delete_event, LV_EVENT_DELETE, entry);
        lv_obj_add_event_cb(entry->screen, page_manager_screen_loaded_event, LV_EVENT_SCREEN_LOADED, entry);
        lv_obj_add_event_cb(entry->screen, page_manager_screen_loaded_event, LV_EVENT_SCREEN_UNLOADED, entry);
    }

    if (add_history && current_page_id != PAGE_MANAGER_NO_PAGE && current_page_id != page_id) {
        page_manager_push_history(current_page_id);
    }

    page_manager_switching = true;
    page_manager_transition_page_id = page_id;
    lv_screen_load_anim(entry->screen, anim_type, anim_time, 0, true);
    if (anim_time == 0) {
        current_page_id = page_id;
        page_manager_transition_page_id = PAGE_MANAGER_NO_PAGE;
        page_manager_switching = false;
    }

    return EP_OK;
}

int page_manager_init(void *app_ctx)
{
    if (page_manager_initialized) {
        page_manager_app_ctx = app_ctx;
        return EP_OK;
    }

    for (size_t i = 0; i < PAGE_MANAGER_MAX_PAGES; ++i) {
        page_entries[i].in_use = false;
        page_entries[i].is_frozen = false;
        page_entries[i].page_id = PAGE_MANAGER_NO_PAGE;
        page_entries[i].screen = NULL;
        page_entries[i].create_cb = NULL;
        page_entries[i].event_cb = NULL;
        page_entries[i].destroy_cb = NULL;
    }

    page_manager_app_ctx = app_ctx;
    current_page_id = PAGE_MANAGER_NO_PAGE;
    page_manager_transition_page_id = PAGE_MANAGER_NO_PAGE;
    page_manager_clear_history();
    page_manager_switching = false;
    page_manager_initialized = true;

    return EP_OK;
}

int page_manager_register(page_manager_page_id_t page_id,
                          page_manager_create_cb_t create_cb,
                          page_manager_event_cb_t event_cb,
                          page_manager_destroy_cb_t destroy_cb)
{
    page_manager_entry_t *entry;

    if (!page_manager_initialized || page_id == PAGE_MANAGER_NO_PAGE || create_cb == NULL) {
        return EP_ERR_INVAL;
    }

    entry = page_manager_find(page_id);
    if (entry == NULL) {
        entry = page_manager_find_free();
    }
    if (entry == NULL) {
        return EP_ERR_UNSUPPORTED;
    }

    entry->in_use = true;
    entry->is_frozen = false;
    entry->page_id = page_id;
    entry->screen = NULL;
    entry->create_cb = create_cb;
    entry->event_cb = event_cb;
    entry->destroy_cb = destroy_cb;

    return EP_OK;
}

int page_manager_switch(page_manager_page_id_t page_id,
                        lv_screen_load_anim_t anim_type,
                        uint32_t anim_time,
                        bool add_history)
{
    return page_manager_load_page(page_id, anim_type, anim_time, add_history);
}

int page_manager_back(lv_screen_load_anim_t anim_type, uint32_t anim_time)
{
    page_manager_page_id_t previous_page_id;

    if (!page_manager_initialized || page_history_count == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    page_history_count--;
    previous_page_id = page_history[page_history_count];
    page_history[page_history_count] = PAGE_MANAGER_NO_PAGE;

    return page_manager_switch(previous_page_id, anim_type, anim_time, false);
}

int page_manager_send_event(page_manager_page_id_t page_id,
                            uint32_t code,
                            uint32_t wparam,
                            uint32_t lparam)
{
    page_manager_entry_t *entry;
    page_manager_page_ctx_t ctx;

    if (!page_manager_initialized || page_id != current_page_id) {
        return EP_ERR_UNSUPPORTED;
    }

    entry = page_manager_find(page_id);
    if (entry == NULL || entry->event_cb == NULL) {
        return EP_ERR_INVAL;
    }

    ctx.app_ctx = page_manager_app_ctx;
    ctx.screen = entry->screen;
    ctx.page_id = page_id;
    entry->event_cb(&ctx, code, wparam, lparam);

    return EP_OK;
}

int page_manager_freeze(page_manager_page_id_t page_id)
{
    page_manager_entry_t *entry;

    entry = page_manager_find(page_id);
    if (entry == NULL) {
        return EP_ERR_INVAL;
    }

    entry->is_frozen = true;

    return EP_OK;
}

int page_manager_unfreeze(page_manager_page_id_t page_id)
{
    page_manager_entry_t *entry;

    entry = page_manager_find(page_id);
    if (entry == NULL) {
        return EP_ERR_INVAL;
    }

    entry->is_frozen = false;

    return EP_OK;
}

page_manager_page_id_t page_manager_current_page_id(void)
{
    return current_page_id;
}
