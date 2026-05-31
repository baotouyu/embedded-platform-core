add_library(ep_components_config STATIC
  src/ep_config.c
)

target_include_directories(ep_components_config
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/components/file/include
)

target_link_libraries(ep_components_config
  PRIVATE
    ep_components_file
)
