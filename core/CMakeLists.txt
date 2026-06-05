add_library(ep_core STATIC
  src/ep_framework.c
)

target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/components/log/include
    ${CMAKE_SOURCE_DIR}/components/config/include
    ${CMAKE_SOURCE_DIR}/components/device/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
    ${CMAKE_SOURCE_DIR}/platforms/include
)
