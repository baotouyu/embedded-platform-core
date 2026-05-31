add_library(ep_app STATIC
  main.c
)

target_include_directories(ep_app
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/components/log/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_app
  PRIVATE
    ep_components_log
    ep_components_event
    ep_components_timer
)
