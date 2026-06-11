add_library(ep_platform_rtos_demo STATIC
  startup/app_start.c
  paths/ep_rtos_platform_paths.c
  osal_port/ep_rtos_osal_stub.c
  hal_port/ep_rtos_hal_stub.c
  component_port/ep_rtos_default_devices.c
  component_port/ep_rtos_component_stub.c
)

target_include_directories(ep_platform_rtos_demo
  PRIVATE
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/components/device/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_platform_rtos_demo
  PRIVATE
    ep_core
    ep_app
    ep_components_device
)
