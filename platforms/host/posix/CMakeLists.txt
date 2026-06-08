find_package(Threads REQUIRED)

add_executable(ep_platform_host_posix
  startup/main.c
  capability/ep_host_platform_capability.c
  paths/ep_host_platform_paths.c
  osal_port/ep_host_osal_stub.c
  osal_port/ep_host_osal_time.c
  osal_port/ep_host_osal_mem.c
  osal_port/ep_host_osal_thread.c
  osal_port/ep_host_osal_mutex.c
  osal_port/ep_host_osal_sem.c
  osal_port/ep_host_osal_queue.c
  hal_port/ep_host_hal_stub.c
  component_port/ep_host_default_devices.c
  component_port/ep_host_component_stub.c
)

target_include_directories(ep_platform_host_posix
  PRIVATE
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/hal/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_platform_host_posix
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
    ep_components_log
    ep_components_config
    ep_components_device
    ep_platform_api
    Threads::Threads
)

add_executable(ep_host_resource_smoke
  demos/resource_smoke_main.c
  paths/ep_host_platform_paths.c
)

target_include_directories(ep_host_resource_smoke
  PRIVATE
    ${CMAKE_SOURCE_DIR}/components/file/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_host_resource_smoke
  PRIVATE
    ep_components_file
    ep_platform_api
)

if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")
  add_executable(ep_host_app
    startup/host_app_main.c
    ui_port/ep_host_ui_port.c
    capability/ep_host_platform_capability.c
    paths/ep_host_platform_paths.c
    osal_port/ep_host_osal_stub.c
    osal_port/ep_host_osal_time.c
    osal_port/ep_host_osal_mem.c
    osal_port/ep_host_osal_thread.c
    osal_port/ep_host_osal_mutex.c
    osal_port/ep_host_osal_sem.c
    osal_port/ep_host_osal_queue.c
    hal_port/ep_host_hal_stub.c
    component_port/ep_host_default_devices.c
    component_port/ep_host_component_stub.c
  )

  target_include_directories(ep_host_app
    PRIVATE
      ${CMAKE_CURRENT_SOURCE_DIR}/ui_port
      ${CMAKE_SOURCE_DIR}/app/ui
      ${CMAKE_SOURCE_DIR}/core/include
      ${CMAKE_SOURCE_DIR}/hal/include
      ${CMAKE_SOURCE_DIR}/osal/include
      ${CMAKE_SOURCE_DIR}/components/log/include
      ${CMAKE_SOURCE_DIR}/components/ui/include
      ${EP_LVGL_INCLUDE_DIR}
  )

  target_compile_definitions(ep_host_app
    PRIVATE
      EP_HAS_HOST_SDL2_UI=1
  )

  target_link_libraries(ep_host_app
    PRIVATE
      ep_core
      ep_app
      ep_components_timer
      ep_components_log
      ep_components_config
      ep_components_device
      ep_components_ui
      ep_platform_api
      ep_thirdparty_lvgl
      Threads::Threads
  )

  target_sources(ep_platform_host_posix
    PRIVATE
      ui_port/ep_host_ui_port.c
  )

  target_include_directories(ep_platform_host_posix
    PRIVATE
      ${CMAKE_CURRENT_SOURCE_DIR}/ui_port
      ${CMAKE_SOURCE_DIR}/app/ui
      ${CMAKE_SOURCE_DIR}/components/ui/include
      ${CMAKE_SOURCE_DIR}/components/log/include
      ${EP_LVGL_INCLUDE_DIR}
  )

  target_compile_definitions(ep_platform_host_posix
    PRIVATE
      EP_HAS_HOST_SDL2_UI=1
  )

  target_link_libraries(ep_platform_host_posix
    PRIVATE
      ep_components_ui
      ep_thirdparty_lvgl
  )

  add_executable(ep_host_lvgl_demo
    demos/lvgl_demo_main.c
    ${CMAKE_SOURCE_DIR}/app/ui/app_ui.c
    ui_port/ep_host_ui_port.c
    osal_port/ep_host_osal_time.c
  )

  target_include_directories(ep_host_lvgl_demo
    PRIVATE
      ${CMAKE_CURRENT_SOURCE_DIR}/ui_port
      ${CMAKE_SOURCE_DIR}/app/ui
      ${CMAKE_SOURCE_DIR}/components/log/include
      ${CMAKE_SOURCE_DIR}/components/ui/include
      ${CMAKE_SOURCE_DIR}/osal/include
      ${EP_LVGL_INCLUDE_DIR}
  )

  target_compile_definitions(ep_host_lvgl_demo
    PRIVATE
      EP_HAS_HOST_SDL2_UI=1
  )

  target_link_libraries(ep_host_lvgl_demo
    PRIVATE
      ep_components_ui
      ep_components_log
      ep_thirdparty_lvgl
  )

  if(TARGET ep_thirdparty_lvgl_demos)
    add_executable(ep_host_lvgl_widgets_demo
      demos/lvgl_widgets_demo_main.c
      ui_port/ep_host_ui_port.c
      osal_port/ep_host_osal_time.c
    )

    target_include_directories(ep_host_lvgl_widgets_demo
      PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/ui_port
        ${CMAKE_SOURCE_DIR}/components/ui/include
        ${CMAKE_SOURCE_DIR}/osal/include
        ${EP_LVGL_INCLUDE_DIR}
    )

    target_compile_definitions(ep_host_lvgl_widgets_demo
      PRIVATE
        EP_HAS_HOST_SDL2_UI=1
    )

    target_link_libraries(ep_host_lvgl_widgets_demo
      PRIVATE
        ep_components_ui
        ep_components_log
        ep_thirdparty_lvgl_demos
    )
  endif()
endif()
