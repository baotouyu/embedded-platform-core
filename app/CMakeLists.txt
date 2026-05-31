add_library(ep_app STATIC
  main.c
)

target_include_directories(ep_app
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/components/log/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_app
  PRIVATE
    ep_components_log
    ep_components_event
    ep_components_timer
)

if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")
  target_include_directories(ep_app
    PRIVATE
      ${CMAKE_SOURCE_DIR}/components/ui/include
      ${CMAKE_SOURCE_DIR}/platforms/host/posix/ui_port
      ${EP_LVGL_INCLUDE_DIR}
  )

  target_compile_definitions(ep_app
    PRIVATE
      EP_HAS_HOST_SDL2_UI=1
  )

  target_link_libraries(ep_app
    PRIVATE
      ep_components_ui
      ep_thirdparty_lvgl
  )
endif()
