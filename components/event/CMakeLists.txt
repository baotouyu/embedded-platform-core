add_library(ep_components_event STATIC
  src/ep_event.c
)

target_include_directories(ep_components_event
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)
