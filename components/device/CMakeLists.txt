add_library(ep_components_device STATIC
  src/ep_device.c
)

target_include_directories(ep_components_device
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_components_device
  PUBLIC
    ep_platform_api
)
