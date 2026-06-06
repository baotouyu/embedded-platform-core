add_library(ep_app_core_export STATIC
  ${CMAKE_SOURCE_DIR}/core/src/ep_framework.c
  ${CMAKE_SOURCE_DIR}/app/app_core.c
  ${CMAKE_SOURCE_DIR}/app/main.c
  ${CMAKE_SOURCE_DIR}/app/selftest/app_selftest.c
  ${CMAKE_SOURCE_DIR}/app/services/beep_service.c
  ${CMAKE_SOURCE_DIR}/app/services/lcd_sleep_service.c
  ${CMAKE_SOURCE_DIR}/app/services/power_board_service.c
  ${CMAKE_SOURCE_DIR}/app/services/rtc_service.c
  ${CMAKE_SOURCE_DIR}/components/config/src/ep_config.c
  ${CMAKE_SOURCE_DIR}/components/event/src/ep_event.c
  ${CMAKE_SOURCE_DIR}/components/file/src/ep_file.c
  ${CMAKE_SOURCE_DIR}/components/log/src/ep_log.c
  ${CMAKE_SOURCE_DIR}/components/timer/src/ep_timer.c
  ${CMAKE_SOURCE_DIR}/components/device/src/ep_device.c
  ${CMAKE_SOURCE_DIR}/components/ui/src/ep_ui.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/startup/app_start.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/osal_port/ep_rtos_osal_stub.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/hal_port/ep_rtos_hal_stub.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/component_port/ep_rtos_component_stub.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/src/elog.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/src/elog_utils.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/port/elog_port.c
)

set_target_properties(ep_app_core_export
  PROPERTIES
    OUTPUT_NAME ep_app_core_export
)

target_include_directories(ep_app_core_export
  PUBLIC
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/app/selftest
    ${CMAKE_SOURCE_DIR}/app/services
    ${CMAKE_SOURCE_DIR}/components/config/include
    ${CMAKE_SOURCE_DIR}/components/device/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/file/include
    ${CMAKE_SOURCE_DIR}/components/log/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
    ${CMAKE_SOURCE_DIR}/components/ui/include
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/hal/include
    ${CMAKE_SOURCE_DIR}/platforms/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/inc
    ${EP_LVGL_INCLUDE_DIR}
)

target_link_libraries(ep_app_core_export
  PRIVATE
    ep_thirdparty_lvgl
)
