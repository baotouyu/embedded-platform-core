cmake_minimum_required(VERSION 3.20)

project(embedded-platform-core C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")

include(ep_options)

# EP_PLATFORM_FAMILY is configured via ep_options.cmake.
add_subdirectory(core)
add_subdirectory(app)
add_subdirectory(components/event)
add_subdirectory(components/timer)
add_subdirectory(components/log)
add_subdirectory(components/file)
add_subdirectory(components/config)
add_subdirectory(platforms/rtos/demo_family)
add_subdirectory(platforms/linux/demo_family)
add_subdirectory(platforms/host/posix)
