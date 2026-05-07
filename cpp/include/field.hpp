#pragma once

#include <iostream>
#include <array>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <bitset>
#include "direction.hpp"


class Field
{
public:
    const uint8_t VISITED = 1;
    const uint8_t NOT_VISITED = 0; 
    const int NO_NEIGHBOUR = -1;
    static const int DIRECTIONS_COUNT = 8;
public:
    Field(int width, int height, int goalWidth);

private:
    int m_width;    // number of vertices in x direction, NOT number of edges
    int m_height;   // number of vertices in y direction, NOT number of edges
    int m_goalWidth; // number of vertices of a goal, including posts
    int m_verticesCount;
    std::vector<uint8_t> m_allowed; //directions in which we can still move
    std::vector<uint8_t> m_visited; //Verticies which were already visited 0 - not visited, 1 - visited
    std::vector<std::array<int, DIRECTIONS_COUNT>> m_neighbours; //look up table which return id of a vertex 
                                                  //to which we will move if we apply a direction on a vertex
    std::vector<int> m_path;

private:
    void allowed_init();
    void visited_init();
    void neighbours_calculate();

};