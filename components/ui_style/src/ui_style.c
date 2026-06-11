#include "ui_style.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"
#include "src/libs/tiny_ttf/lv_tiny_ttf.h"

#include <stdbool.h>
#include <stddef.h>

#define UI_STYLE_FONT_FILE_NAME "SourceHan-Regular_arial_cn.ttf"
#define UI_STYLE_FONT_CACHE_SIZE (64u * 1024u)

typedef struct {
    ui_style_font_id_t id;
    int32_t size;
    lv_font_t *font;
} ui_style_font_entry_t;

static bool ui_style_initialized;
static ui_style_font_entry_t ui_style_fonts[UI_STYLE_FONT_COUNT] = {
    {UI_STYLE_FONT_HOME_SIDE, 24, NULL},
    {UI_STYLE_FONT_HOME_USER, 28, NULL},
    {UI_STYLE_FONT_HOME_CENTER, 40, NULL},
};

static ui_style_font_entry_t *ui_style_find_entry(ui_style_font_id_t font_id)
{
    for (size_t i = 0u; i < UI_STYLE_FONT_COUNT; ++i) {
        if (ui_style_fonts[i].id == font_id) {
            return &ui_style_fonts[i];
        }
    }

    return NULL;
}

void ui_style_deinit(void)
{
    for (size_t i = 0u; i < UI_STYLE_FONT_COUNT; ++i) {
        if (ui_style_fonts[i].font != NULL) {
            lv_tiny_ttf_destroy(ui_style_fonts[i].font);
            ui_style_fonts[i].font = NULL;
        }
    }
    ui_style_initialized = false;
}

int ui_style_init(void)
{
    char font_path[160];
    int rc;

    if (ui_style_initialized) {
        return EP_OK;
    }

    rc = ep_platform_font_path(UI_STYLE_FONT_FILE_NAME, font_path, sizeof(font_path));
    if (rc != EP_OK) {
        return rc;
    }

    lv_tiny_ttf_init();
    for (size_t i = 0u; i < UI_STYLE_FONT_COUNT; ++i) {
        ui_style_fonts[i].font = lv_tiny_ttf_create_file_ex(
            font_path,
            ui_style_fonts[i].size,
            UI_STYLE_FONT_CACHE_SIZE);
        if (ui_style_fonts[i].font == NULL) {
            ui_style_deinit();
            return EP_ERR_BUSY;
        }
    }

    ui_style_initialized = true;
    return EP_OK;
}

const lv_font_t *ui_style_font(ui_style_font_id_t font_id)
{
    ui_style_font_entry_t *entry;

    entry = ui_style_find_entry(font_id);
    if (entry == NULL || entry->font == NULL) {
        return LV_FONT_DEFAULT;
    }

    return entry->font;
}
