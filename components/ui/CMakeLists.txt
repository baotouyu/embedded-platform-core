add_library(ep_components_ui STATIC
  src/ep_ui.c
)

target_include_directories(ep_components_ui
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../../osal/include
)

target_link_libraries(ep_components_ui
  PRIVATE
    ep_thirdparty_lvgl
)
