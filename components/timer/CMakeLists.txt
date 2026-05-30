add_library(ep_components_timer STATIC
  src/ep_timer.c
)

target_include_directories(ep_components_timer
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_components_timer
  PUBLIC
    ep_components_event
)
