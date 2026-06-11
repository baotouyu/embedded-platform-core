add_library(ep_components_recipe_parser STATIC
  src/ep_simple_recipe.c
)

target_include_directories(ep_components_recipe_parser
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/../../osal/include
)

target_link_libraries(ep_components_recipe_parser
  PRIVATE
    ep_thirdparty_cjson
    ep_thirdparty_sqlite
)
