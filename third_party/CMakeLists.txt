add_library(ep_thirdparty_cjson STATIC
  external/cjson/cJSON.c
)

target_include_directories(ep_thirdparty_cjson
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/external/cjson
)

add_library(ep_thirdparty_sqlite STATIC
  external/sqlite/sqlite3.c
)

target_include_directories(ep_thirdparty_sqlite
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/external/sqlite
)
