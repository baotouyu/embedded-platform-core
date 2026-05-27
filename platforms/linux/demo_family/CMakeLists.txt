add_executable(ep_platform_linux_demo
  startup/main.c
  osal_port/ep_linux_osal_stub.c
  hal_port/ep_linux_hal_stub.c
  component_port/ep_linux_component_stub.c
)
