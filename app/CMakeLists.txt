add_library(ep_app STATIC
  main.c
)

target_include_directories(ep_app
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
