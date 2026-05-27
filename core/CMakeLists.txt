add_library(ep_core STATIC
  src/ep_framework.c
)

target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/app/include
)
