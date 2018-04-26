cmake_minimum_required(VERSION 3.0)
project(jnl)

file(GLOB_RECURSE sources       src/main/*.cpp src/main/*.h)
file(GLOB_RECURSE sources_test  src/test/*.cpp)
file(GLOB_RECURSE data          resources/*)

add_executable(jnl ${sources} ${data})

target_compile_options(jnl PUBLIC -std=c++1y -Wall -Wfloat-conversion)

# this lets me include files relative to the root src dir with a <> pair
# target_include_directories(example PUBLIC src/main)

# this copies all resource files in the build directory
# we need this, because we want to work with paths relative to the executable
file(COPY ${data} DESTINATION resources)

# this defines the variables Boost_LIBRARIES that contain all library names
# that we need to link to
find_package(Boost 1.36.0 COMPONENTS filesystem system REQUIRED)

target_link_libraries(jnl PUBLIC
  ${Boost_LIBRARIES}
  # here you can add any library dependencies
)

# this is for our testing framework
# we don't add REQUIRED because it's just for testing
find_package(GTest)

add_executable(unit_tests ${sources_test} ${sources})
target_compile_definitions(unit_tests PUBLIC UNIT_TESTS)
set_target_properties(jnl PROPERTIES ENABLE_EXPORTS on)
target_link_libraries(unit_tests PUBLIC
  ${GTEST_BOTH_LIBRARIES}
  jnl
)

target_include_directories(unit_tests PUBLIC
  ${GTEST_INCLUDE_DIRS} # doesn't do anything on Linux
)


install(TARGETS jnl DESTINATION jnl_destination)
# this is basically a repeat of the file copy instruction that copies the
# resources in the build directory, but here we tell cmake that we want it
# in the package
install(DIRECTORY resources DESTINATION jnl_destination)

set(CPACK_PACKAGE_NAME "jnl")
set(CPACK_PACKAGE_VERSION "1.0.0")

# we don't want to split our program up into several things
set(CPACK_MONOLITHIC_INSTALL 1)

# This must be last
include(CPack)