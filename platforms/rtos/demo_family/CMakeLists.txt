add_library(ep_platform_rtos_demo STATIC
  startup/app_start.c
  osal_port/ep_rtos_osal_stub.c
  hal_port/ep_rtos_hal_stub.c
  component_port/ep_rtos_component_stub.c
)

target_include_directories(ep_platform_rtos_demo
  PRIVATE
    ${CMAKE_SOURCE_DIR}/core/include
)

target_link_libraries(ep_platform_rtos_demo
  PRIVATE
    ep_core
    ep_app
)
