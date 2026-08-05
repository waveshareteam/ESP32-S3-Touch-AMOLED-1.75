idf_component_register(
    SRCS "avi_player.c" "avifile.c"
    INCLUDE_DIRS "include"
    REQUIRES esp_timer
)

# Keep the public 2.0.0 version contract without pulling cmake_utilities into
# this local, reproducible override.
target_compile_definitions(${COMPONENT_LIB} PRIVATE
    AVI_PLAYER_VER_MAJOR=2
    AVI_PLAYER_VER_MINOR=0
    AVI_PLAYER_VER_PATCH=0
)

target_compile_options(${COMPONENT_LIB} PRIVATE "-Wno-implicit-fallthrough")
