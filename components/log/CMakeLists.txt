add_library(ep_components_log STATIC
  src/ep_log.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/src/elog.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/src/elog_utils.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/port/elog_port.c
)

target_include_directories(ep_components_log
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/inc
)
