set(EP_LVGL_PACKAGE "host_macos" CACHE STRING "LVGL prebuilt package name")

if(NOT DEFINED EP_PROJECT_ROOT)
  set(EP_PROJECT_ROOT "${CMAKE_CURRENT_LIST_DIR}/../..")
endif()

get_filename_component(EP_PROJECT_ROOT "${EP_PROJECT_ROOT}" ABSOLUTE)

set(EP_LVGL_ROOT "${EP_PROJECT_ROOT}/third_party/prebuilt/lvgl/${EP_LVGL_PACKAGE}")
set(EP_LVGL_INCLUDE_DIR "${EP_LVGL_ROOT}/include")
set(EP_LVGL_LIBRARY "${EP_LVGL_ROOT}/lib/liblvgl.a")
set(EP_LVGL_MANIFEST "${EP_LVGL_ROOT}/lvgl_package.txt")

if(NOT EXISTS "${EP_LVGL_MANIFEST}")
  message(FATAL_ERROR "LVGL manifest not found: ${EP_LVGL_MANIFEST}")
endif()

if(NOT EXISTS "${EP_LVGL_INCLUDE_DIR}/lvgl.h")
  message(FATAL_ERROR "LVGL header not found: ${EP_LVGL_INCLUDE_DIR}/lvgl.h")
endif()

if(NOT EXISTS "${EP_LVGL_INCLUDE_DIR}/lv_conf.h")
  message(FATAL_ERROR "LVGL config not found: ${EP_LVGL_INCLUDE_DIR}/lv_conf.h")
endif()

if(NOT EXISTS "${EP_LVGL_LIBRARY}")
  message(FATAL_ERROR "LVGL static library not found: ${EP_LVGL_LIBRARY}")
endif()

file(READ "${EP_LVGL_MANIFEST}" EP_LVGL_MANIFEST_TEXT)
if(NOT EP_LVGL_MANIFEST_TEXT MATCHES "lvgl.version=9\\.1\\.")
  message(FATAL_ERROR "LVGL package must use LVGL 9.1.x: ${EP_LVGL_MANIFEST}")
endif()

if(NOT TARGET ep_thirdparty_lvgl)
  add_library(ep_thirdparty_lvgl STATIC IMPORTED GLOBAL)
  set_target_properties(ep_thirdparty_lvgl PROPERTIES
    IMPORTED_LOCATION "${EP_LVGL_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${EP_LVGL_INCLUDE_DIR}"
  )
endif()
