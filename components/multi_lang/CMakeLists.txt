add_library(ep_components_multi_lang STATIC
  src/multi_lang.c
)

target_include_directories(ep_components_multi_lang
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../../osal/include
)

target_link_libraries(ep_components_multi_lang
  PRIVATE
    ep_thirdparty_cjson
    ep_thirdparty_sqlite
)
