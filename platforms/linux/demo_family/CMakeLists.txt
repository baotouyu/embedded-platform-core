add_executable(ep_platform_linux_demo
  startup/main.c
  osal_port/ep_linux_osal_stub.c
  hal_port/ep_linux_hal_stub.c
  component_port/ep_linux_component_stub.c
)

target_include_directories(ep_platform_linux_demo
  PRIVATE
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_platform_linux_demo
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
)
