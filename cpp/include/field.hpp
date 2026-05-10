#pragma once

#include <iostream>
#include <array>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <bitset>

#include "direction.hpp"
#include "types.hpp"


class Field
{
public:
    Field(int width, int height, int goalWidth);
    //const Positions& positions() ? 

    int vertices_count() const;
    const AllowedDirections& initial_allowed_directions() const;
    const VertexFlags& border_flags() const;

    VertexId neighbour_at(VertexId id, Direction::Index direction) const;
    bool is_initial_direction_allowed(VertexId, Direction::Index direction) const;


private:
    int m_width;     // number of vertices in x direction, NOT number of edges
    int m_height;    // number of vertices in y direction, NOT number of edges
    int m_goalWidth; // number of vertices of a goal, including posts
    int m_verticesCount;

    AllowedDirections m_initialAllowedDirections; //mask of directions in which we can still move from each vertex
    
    VertexFlags m_borderFlags; //Flags on each vertices which are part of the border -> false - not border, true - border

    Neighbours m_neighbours; //look up table which returns VertexId, usage: [VertexId][int] where int represents direction
                                //to which we will move if we apply a direction on a vertex

    struct Positions
    {
        VertexId upperGoalId;  //beginning of upper goal (left side)
        VertexId lowerGoalId; //beginning of lower goal (left side)

        VertexId topLeftCorner;
        VertexId topRightCorner; 
        VertexId bottomLeftCorner; 
        VertexId bottomRightCorner;

        VertexId topLeftGoalPost;
        VertexId topRightGoalPost; 
        VertexId bottomLeftGoalPost; 
        VertexId bottomRightGoalPost;

        VertexId insideTopLeftCorner;
        VertexId insideTopRightCorner; 
        VertexId insideBottomLeftCorner; 
        VertexId insideBottomRightCorner;

        VertexId fieldMiddle;
    };
    Positions m_pos;

private:
    static int validated_width(int width);
    static int validated_height(int height);
    static int validated_goal_width(int goalWidth, int validWidth); //assumes already valid width!

    static Positions calculate_positions(int width, int height, int goalWidth, int verticesCount);

    void initialize_allowed();
    void initialize_allowed_vertical_borders();
    void initialize_allowed_top_border();
    void initialize_allowed_bottom_border();
    void initialize_allowed_inside();
    
    void calculate_border();
    
    void calculate_neighbours();
    void calculate_regular_neighbours();
    void fix_goal_area_neighbours();

};