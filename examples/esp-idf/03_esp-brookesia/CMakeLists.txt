# For more information about build system see
# https://docs.espressif.com/projects/esp-idf/en/latest/api-guides/build-system.html
# The following five lines of boilerplate have to be in your project's
# CMakeLists in this exact order for cmake to work correctly
cmake_minimum_required(VERSION 3.5)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(esp-brookesia)

if(DEFINED IDF_VERSION_MAJOR AND IDF_VERSION_MAJOR GREATER_EQUAL 6)
    # TODO: Remove after esp-boost is warning-clean with ESP-IDF v6/GCC 15.
    idf_build_set_property(
        CXX_COMPILE_OPTIONS
            "-Wno-error=deprecated-variadic-comma-omission"
        APPEND
    )
endif()
