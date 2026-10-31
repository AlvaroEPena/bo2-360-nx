# Adds bo2-zm-nx's host tools to a ReXGlue SDK build without editing the SDK.
# Pass to the SDK configure as:
#   -DCMAKE_PROJECT_ReXGlue_INCLUDE=<repository>/cmake/host_tools_inject.cmake
# The include is deferred to the end of the SDK's top-level CMakeLists, so
# every rex:: target exists by then. (Deferred calls may not add_subdirectory.)
get_filename_component(SWITCH_BO2_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
cmake_language(DEFER DIRECTORY "${CMAKE_SOURCE_DIR}"
    CALL include "${SWITCH_BO2_ROOT}/tools/xexdump/CMakeLists.txt")
