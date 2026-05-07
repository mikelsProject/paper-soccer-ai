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
    Field(int width, int height, int goalWidth);

private:
    const std::uint8_t Visited = 1;
    const std::uint8_t NotVisited = 0; 
    const int NoNeighbour = -1;
    
private:
    int m_width;    // number of vertices in x direction, NOT number of edges
    int m_height;   // number of vertices in y direction, NOT number of edges
    int m_goalWidth; // number of vertices of a goal, including posts
    int m_verticesCount;

    std::vector<std::uint8_t> m_allowed; //directions in which we can still move
    std::vector<std::uint8_t> m_visited; //Verticies which were already visited 0 - not visited, 1 - visited
    std::vector<std::array<int, Direction::count>> m_neighbours; //look up table which return id of a vertex 
                                                  //to which we will move if we apply a direction on a vertex
    std::vector<int> m_path;

    struct Positions
    {
        int upperGoalId;  //beginning of upper goal (left side)
        int lowerGoalId; //beginning of lower goal (left side)

        int topLeftCorner;
        int topRightCorner; 
        int bottomLeftCorner; 
        int bottomRightCorner;

        int topLeftGoalPost;
        int topRightGoalPost; 
        int bottomLeftGoalPost; 
        int bottomRightGoalPost;

        int insideTopLeftCorner;
        int insideTopRightCorner; 
        int insideBottomLeftCorner; 
        int insideBottomRightCorner;

        int fieldMiddle;
    };
    Positions m_pos;

private:
    static int validated_width(int width);
    static int validated_height(int height);
    static int validated_goal_width(int goalWidth, int validWidth); //assumes already valid width!

    void calculate_positions();


    void initialize_allowed();
    void initialize_allowed_vertical_borders();
    void initialize_allowed_top_border();
    void initialize_allowed_bottom_border();
    void initialize_allowed_inside();
    
    

    void initialize_visited();
    
    void calculate_neighbours();
    void calculate_regular_neighbours();
    void fix_goal_area_neighbours();


};