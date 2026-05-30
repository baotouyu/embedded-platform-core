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
    ep_components_event
    Threads::Threads
)
