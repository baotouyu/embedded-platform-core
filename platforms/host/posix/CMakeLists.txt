find_package(Threads REQUIRED)

add_executable(ep_platform_host_posix
  startup/main.c
  osal_port/ep_host_osal_stub.c
  osal_port/ep_host_osal_time.c
  osal_port/ep_host_osal_mem.c
  osal_port/ep_host_osal_thread.c
  osal_port/ep_host_osal_mutex.c
  osal_port/ep_host_osal_sem.c
  osal_port/ep_host_osal_queue.c
  hal_port/ep_host_hal_stub.c
  component_port/ep_host_component_stub.c
)

target_include_directories(ep_platform_host_posix
  PRIVATE
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_platform_host_posix
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
    ep_components_log
    ep_components_config
    Threads::Threads
)

if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")
  target_sources(ep_platform_host_posix
    PRIVATE
      ui_port/ep_host_ui_port.c
  )

  target_include_directories(ep_platform_host_posix
    PRIVATE
      ${CMAKE_CURRENT_SOURCE_DIR}/ui_port
  )

  target_compile_definitions(ep_platform_host_posix
    PRIVATE
      EP_HAS_HOST_SDL2_UI=1
  )

  target_link_libraries(ep_platform_host_posix
    PRIVATE
      ep_components_ui
  )
endif()
