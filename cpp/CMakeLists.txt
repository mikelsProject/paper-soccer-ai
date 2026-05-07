cmake_minimum_required(VERSION 3.16)

project(paper_soccer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(soccer
    src/field.cpp
    src/game.cpp
    src/main.cpp
)

target_include_directories(soccer PRIVATE include) 