cmake_minimum_required(VERSION 3.20)
project(r3xa_graphviz_wasi LANGUAGES C)

if(NOT DEFINED GRAPHVIZ_SOURCE_DIR)
  message(FATAL_ERROR "GRAPHVIZ_SOURCE_DIR must point to the pinned Graphviz source tree")
endif()

set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(GRAPHVIZ_CLI OFF CACHE BOOL "" FORCE)
set(ENABLE_LTDL OFF CACHE STRING "" FORCE)
set(WITH_EXPAT OFF CACHE STRING "" FORCE)
set(WITH_ZLIB OFF CACHE STRING "" FORCE)
set(WITH_GVEDIT OFF CACHE STRING "" FORCE)
set(WITH_SMYRNA OFF CACHE STRING "" FORCE)
set(ENABLE_TCL OFF CACHE STRING "" FORCE)
set(ENABLE_SWIG OFF CACHE STRING "" FORCE)
set(ENABLE_SHARP OFF CACHE STRING "" FORCE)
set(ENABLE_D OFF CACHE STRING "" FORCE)
set(ENABLE_GO OFF CACHE STRING "" FORCE)
set(ENABLE_GUILE OFF CACHE STRING "" FORCE)
set(ENABLE_JAVA OFF CACHE STRING "" FORCE)
set(ENABLE_JAVASCRIPT OFF CACHE STRING "" FORCE)
set(ENABLE_LUA OFF CACHE STRING "" FORCE)
set(ENABLE_PERL OFF CACHE STRING "" FORCE)
set(ENABLE_PHP OFF CACHE STRING "" FORCE)
set(ENABLE_PYTHON OFF CACHE STRING "" FORCE)
set(ENABLE_R OFF CACHE STRING "" FORCE)
set(with_cxx_api OFF CACHE BOOL "" FORCE)
set(with_cxx_tests OFF CACHE BOOL "" FORCE)
set(with_digcola OFF CACHE BOOL "" FORCE)
set(with_ipsepcola OFF CACHE BOOL "" FORCE)
set(with_ortho OFF CACHE BOOL "" FORCE)
set(with_sfdp OFF CACHE BOOL "" FORCE)

# Graphviz uses signal.h and times() in its common libraries. WASI exposes
# these through explicitly opt-in emulation libraries in the SDK.
add_compile_definitions(
  _WASI_EMULATED_SIGNAL
  _WASI_EMULATED_PROCESS_CLOCKS
)
add_compile_options(-include unistd.h)

add_subdirectory("${GRAPHVIZ_SOURCE_DIR}" graphviz EXCLUDE_FROM_ALL)

add_executable(r3xa_graphviz wrapper.c)
target_include_directories(r3xa_graphviz PRIVATE
  "${GRAPHVIZ_SOURCE_DIR}/lib"
  "${CMAKE_BINARY_DIR}/graphviz"
)
target_link_libraries(r3xa_graphviz PRIVATE
  cdt
  cgraph
  gvc
  gvplugin_core
  gvplugin_dot_layout
  gvplugin_vt
  pathplan
  xdot
)
target_link_options(r3xa_graphviz PRIVATE
  "-lwasi-emulated-signal"
  "-lwasi-emulated-process-clocks"
  "-Wl,--no-entry"
  "-Wl,--export-memory"
  "-Wl,--export=malloc"
  "-Wl,--export=free"
  "-Wl,--export=r3xa_graphviz_free"
  "-Wl,--export=r3xa_graphviz_render"
  "-Wl,--export=r3xa_graphviz_last_error"
)
set_target_properties(
  r3xa_graphviz
  PROPERTIES
    OUTPUT_NAME "graphviz-12.2.1"
    SUFFIX ".wasm"
)
