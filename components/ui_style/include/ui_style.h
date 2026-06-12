#ifndef UI_STYLE_H
#define UI_STYLE_H

#include "lvgl.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    UI_STYLE_FONT_DETAILS_MENU_VALUE = 0,
    UI_STYLE_FONT_DETAILS_DRINK,
    UI_STYLE_FONT_DETAILS_MENU_TITLE,
    UI_STYLE_FONT_DETAILS_MODAL,
    UI_STYLE_FONT_HOME_SIDE,
    UI_STYLE_FONT_HOME_USER,
    UI_STYLE_FONT_HOME_CENTER,
    UI_STYLE_FONT_COUNT
} ui_style_font_id_t;

int ui_style_init(void);
const lv_font_t *ui_style_font(ui_style_font_id_t font_id);
void ui_style_deinit(void);

#ifdef __cplusplus
}
#endif

#endif
