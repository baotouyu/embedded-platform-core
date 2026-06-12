add_library(ep_components_ui_style STATIC
  src/ui_style.c
  src/ui_font_source_han_18.c
  src/ui_font_source_han_20.c
  src/ui_font_source_han_24.c
  src/ui_font_source_han_28.c
  src/ui_font_source_han_32.c
  src/ui_font_source_han_40.c
)

target_include_directories(ep_components_ui_style
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/platforms/include
    ${EP_LVGL_INCLUDE_DIR}
)

target_link_libraries(ep_components_ui_style
  PRIVATE
    ep_thirdparty_lvgl
)
