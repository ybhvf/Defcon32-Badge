# Create an INTERFACE library for our C module.
add_library(ziatv_ext INTERFACE)

# Add our source files to the lib
target_sources(ziatv_ext INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/sstv.c
    ${CMAKE_CURRENT_LIST_DIR}/modem.c
)

# Add the current directory as an include directory.
target_include_directories(ziatv_ext INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

# target_compile_options(ziatv_ext INTERFACE -funsafe-math-optimizations)

# Link our INTERFACE library to the usermod target.
target_link_libraries(usermod INTERFACE ziatv_ext)
