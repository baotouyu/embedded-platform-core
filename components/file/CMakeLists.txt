add_library(ep_components_file STATIC
  src/ep_file.c
)

target_include_directories(ep_components_file
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)
