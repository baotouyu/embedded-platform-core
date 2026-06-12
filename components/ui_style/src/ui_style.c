#include "ui_style.h"

#include "ep_osal_err.h"
#include "ep_platform_paths.h"

#if LV_USE_FREETYPE
#include "src/libs/freetype/lv_freetype.h"
#endif

#include <stddef.h>

#define UI_STYLE_FONT_FILE_NAME "SourceHan-Regular_arial_cn.ttf"

LV_FONT_DECLARE(ui_font_source_han_18)
LV_FONT_DECLARE(ui_font_source_han_20)
LV_FONT_DECLARE(ui_font_source_han_24)
LV_FONT_DECLARE(ui_font_source_han_28)
LV_FONT_DECLARE(ui_font_source_han_32)
LV_FONT_DECLARE(ui_font_source_han_40)

typedef struct {
    ui_style_font_id_t id;
    uint32_t size;
    const lv_font_t *font;
#if LV_USE_FREETYPE
    lv_font_t *freetype_font;
#endif
} ui_style_font_entry_t;

static ui_style_font_entry_t ui_style_fonts[UI_STYLE_FONT_COUNT] = {
    {UI_STYLE_FONT_DETAILS_MENU_VALUE, 18u, &ui_font_source_han_18, NULL},
    {UI_STYLE_FONT_DETAILS_DRINK, 20u, &ui_font_source_han_20, NULL},
    {UI_STYLE_FONT_DETAILS_MENU_TITLE, 20u, &ui_font_source_han_20, NULL},
    {UI_STYLE_FONT_DETAILS_MODAL, 32u, &ui_font_source_han_32, NULL},
    {UI_STYLE_FONT_HOME_SIDE, 24u, &ui_font_source_han_24, NULL},
    {UI_STYLE_FONT_HOME_USER, 28u, &ui_font_source_han_28, NULL},
    {UI_STYLE_FONT_HOME_CENTER, 40u, &ui_font_source_han_40, NULL},
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

#if LV_USE_FREETYPE
static void ui_style_restore_static_fonts(void)
{
    ui_style_fonts[UI_STYLE_FONT_DETAILS_MENU_VALUE].font = &ui_font_source_han_18;
    ui_style_fonts[UI_STYLE_FONT_DETAILS_DRINK].font = &ui_font_source_han_20;
    ui_style_fonts[UI_STYLE_FONT_DETAILS_MENU_TITLE].font = &ui_font_source_han_20;
    ui_style_fonts[UI_STYLE_FONT_DETAILS_MODAL].font = &ui_font_source_han_32;
    ui_style_fonts[UI_STYLE_FONT_HOME_SIDE].font = &ui_font_source_han_24;
    ui_style_fonts[UI_STYLE_FONT_HOME_USER].font = &ui_font_source_han_28;
    ui_style_fonts[UI_STYLE_FONT_HOME_CENTER].font = &ui_font_source_han_40;
}
#endif

void ui_style_deinit(void)
{
#if LV_USE_FREETYPE
    for (size_t i = 0u; i < UI_STYLE_FONT_COUNT; ++i) {
        if (ui_style_fonts[i].freetype_font != NULL) {
            lv_freetype_font_delete(ui_style_fonts[i].freetype_font);
            ui_style_fonts[i].freetype_font = NULL;
        }
    }
    ui_style_restore_static_fonts();
#endif
}

int ui_style_init(void)
{
#if LV_USE_FREETYPE
    char font_path[160];
    int rc;

    if (ui_style_fonts[0].freetype_font != NULL) {
        return EP_OK;
    }

    rc = ep_platform_font_path(UI_STYLE_FONT_FILE_NAME, font_path, sizeof(font_path));
    if (rc != EP_OK) {
        return rc;
    }

    for (size_t i = 0u; i < UI_STYLE_FONT_COUNT; ++i) {
        ui_style_fonts[i].freetype_font = lv_freetype_font_create(
            font_path,
            LV_FREETYPE_FONT_RENDER_MODE_BITMAP,
            ui_style_fonts[i].size,
            LV_FREETYPE_FONT_STYLE_NORMAL);
        if (ui_style_fonts[i].freetype_font == NULL) {
            ui_style_deinit();
            return EP_ERR_BUSY;
        }

        ui_style_fonts[i].font = ui_style_fonts[i].freetype_font;
    }
#endif

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
