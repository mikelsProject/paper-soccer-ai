#include "include/field.hpp"

int Field::validated_width(int width)
{
    if(width >= 5 && width % 2 == 1)
        return width;
    else
    {
        std::cout << "width has to be an odd number, at least 5\n";
        std::cout << "width was set to 9\n";
        return 9;
    }
}

int Field::validated_height(int height)
{
    if(height >= 3 && height % 2 == 1)
        return height;
    else
    {
        std::cout << "height has to be an odd number, at least 3";
        std::cout << "height was set to default 13";
        return 13;
    }
}

int Field::validated_goal_width(int goalWidth, int validWidth)
{
    if(goalWidth >= 3 && goalWidth <= validWidth - 2 && goalWidth % 2 == 1)
        return goalWidth;
    else
    {
        std::cout << "goal width has to be an odd number, at least 3, smaller than width of the whole field";
        std::cout << "goal width was set to defualt 3";
        return 3;
    }
}

void Field::calculate_positions()
{
    //beginning of upper goal (left side)
    m_pos.upperGoalId = 0;
    //beginning of lower goal (left side)
    m_pos.lowerGoalId = m_verticesCount - m_goalWidth; 
    
    //field corners
    m_pos.topLeftCorner = m_goalWidth;
    m_pos.topRightCorner = m_goalWidth + m_width - 1;
    m_pos.bottomLeftCorner = m_goalWidth + m_width * (m_height - 1);
    m_pos.bottomRightCorner = m_goalWidth + m_width * m_height - 1;

    //goals posts
    m_pos.topLeftGoalPost = m_goalWidth + (m_width - m_goalWidth) / 2;
    m_pos.topRightGoalPost = m_pos.topLeftGoalPost + m_goalWidth - 1;
    m_pos.bottomLeftGoalPost = m_pos.bottomLeftCorner + (m_width - m_goalWidth) / 2;
    m_pos.bottomRightGoalPost = m_pos.bottomLeftGoalPost + m_goalWidth - 1;

    //corners of the field part without borders
    m_pos.insideTopLeftCorner = m_pos.topLeftCorner + m_width + 1;
    m_pos.insideTopRightCorner = m_pos.topRightCorner + m_width - 1;
    m_pos.insideBottomLeftCorner = m_pos.bottomLeftCorner - m_width + 1;
    m_pos.insideBottomRightCorner = m_pos.bottomRightCorner - m_width - 1;

    m_pos.fieldMiddle = (m_goalWidth - 1)/2 + m_width * (m_height + 1)/2;
}

Field::Field(int width, int height, int goalWidth)
    :m_width(validated_width(width)), 
     m_height(validated_height(height)),
     m_goalWidth(validated_goal_width(goalWidth, m_width)),
     m_verticesCount(m_width * m_height + 2 * goalWidth)
{
    initialize_allowed();
    initialize_visited();
}


void Field::initialize_allowed_vertical_borders()
{
    namespace Dir = Direction;
    //left border without corners
    for(int id = m_pos.topLeftCorner + m_width; id <= m_pos.bottomLeftCorner - m_width; id += m_width)
        m_allowed[id] |= Dir::UpRightMask | Dir::RightMask | Dir::DownRightMask;

    //right border without corners
    for(int id = m_pos.topRightCorner + m_width; id <= m_pos.bottomRightCorner - m_width; id += m_width)
        m_allowed[id] |= Dir::UpLeftMask | Dir::LeftMask | Dir::DownLeftMask;
}

void Field::initialize_allowed_top_border()
{
    namespace Dir = Direction;
    //upper border without corners
    
    for(int id = m_pos.topLeftCorner + 1; id < m_pos.topLeftGoalPost; ++id)
        m_allowed[id] |= Dir::DownLeftMask | Dir::DownMask | Dir::DownRightMask;
    
        //goal area
    m_allowed[m_pos.topLeftGoalPost] |= Dir::DownLeftMask | Dir::DownMask | Dir::DownRightMask | Dir::RightMask | Dir::UpRightMask;

    for(int id = m_pos.topLeftGoalPost + 1; id < m_pos.topRightGoalPost; ++id)
        m_allowed[id] |= Dir::All;

    m_allowed[m_pos.topRightGoalPost] |= Dir::UpLeftMask | Dir::LeftMask | Dir::DownLeftMask | Dir::DownMask | Dir::DownRightMask;
        //

    for(int id = m_pos.topRightGoalPost + 1; id < m_pos.topRightCorner; ++id)
        m_allowed[id] |= Dir::DownLeftMask | Dir::DownMask | Dir::DownRightMask;
    
}

void Field::initialize_allowed_bottom_border()
{
    namespace Dir = Direction;
    //lower border without corners

    for(int id = m_pos.bottomLeftCorner + 1; id < m_pos.bottomLeftGoalPost; ++id)
        m_allowed[id] |= Dir::UpLeftMask | Dir::UpMask | Dir::UpRightMask;
    
        //goal area
    m_allowed[m_pos.bottomLeftGoalPost] |= Dir::UpLeftMask | Dir::UpMask | Dir::UpRightMask | Dir::RightMask | Dir::DownRightMask;

    for(int id = m_pos.bottomLeftGoalPost + 1; id < m_pos.bottomRightGoalPost; ++id)
        m_allowed[id] |= Dir::All;

    m_allowed[m_pos.bottomRightGoalPost] |= Dir::DownLeftMask | Dir::LeftMask | Dir::UpLeftMask | Dir::UpMask | Dir::UpRightMask;
        //

    for(int id = m_pos.bottomRightGoalPost + 1; id <= m_pos.bottomRightCorner - 1; ++id)
        m_allowed[id] |= Dir::UpLeftMask | Dir::UpMask | Dir::UpRightMask;

}

void Field::initialize_allowed_inside()
{
    namespace Dir = Direction;

    const int insideWidth = m_width - 2;
    const int insideHeight = m_height - 2;

    for(int localY = 0; localY < insideHeight; ++localY)
    {
        for(int localX = 0; localX < insideWidth; ++localX)
        {
            m_allowed[m_pos.insideTopLeftCorner + localX + m_width * localY] = Dir::All;
        }
    }
    
        //but corners of the field are not allowed to be moved into
    m_allowed[m_pos.insideTopLeftCorner] &= ~Dir::UpLeftMask;
    m_allowed[m_pos.insideTopRightCorner] &= ~Dir::UpRightMask;
    m_allowed[m_pos.insideBottomLeftCorner] &= ~Dir::DownLeftMask;
    m_allowed[m_pos.insideBottomRightCorner] &= ~Dir::DownRightMask;
}

void Field::initialize_allowed()
{
    namespace Dir = Direction;
    m_allowed.assign(m_verticesCount, Dir::None);
    
    // Corners and score fields remain NONE intentionally.
    // The code below only adds directions to playable border/interior fields.

    initialize_allowed_vertical_borders();
    initialize_allowed_top_border();
    initialize_allowed_bottom_border();
    initialize_allowed_inside();
}


void Field::initialize_visited()
{
    m_visited.assign(m_verticesCount, NotVisited);
    m_visited[m_pos.fieldMiddle] = Visited;   
}


void Field::calculate_regular_neighbours()
{
    const std::array<int, Direction::count> directionOffset = 
    { 
        -m_width,      // 0 -> Up
        -m_width + 1,  // 1 -> UpRight
        1,             // 2 -> Right
        m_width + 1,   // 3 -> DownRight
        m_width,       // 4 -> Down
        m_width - 1,   // 5 -> DownLeft
        -1,            // 6 -> Left
        -m_width - 1   // 7 -> UpLeft
    };

    for(int id = 0; id < m_verticesCount; ++id)
    {   
        for(int direction = 0; direction < Direction::count; ++direction)
        {
            //is the bit for current direction set to 1 (allowed)
            bool directionAllowed = m_allowed[id] & (1u << direction) != 0;

            if(directionAllowed)
            {
                m_neighbours[id][direction] =  id + directionOffset[direction];
            }
            else
            {
                m_neighbours[id][direction] = NoNeighbour;
            }
        }      
    }
}

void Field::fix_goal_area_neighbours()
{
    const int correction = (m_width - m_goalWidth) / 2;
    
    //top are near goal
    m_neighbours[m_pos.topLeftGoalPost][Direction::UpRight] += correction;
    for(int id = m_pos.topLeftGoalPost + 1; id < m_pos.topRightGoalPost; ++id)
    {  
        m_neighbours[id][Direction::Up] += correction;
        m_neighbours[id][Direction::UpRight] += correction;
        m_neighbours[id][Direction::UpLeft] += correction;
    }
    m_neighbours[m_pos.topRightGoalPost][Direction::UpLeft] += correction; 

    //bottom area near goal
    m_neighbours[m_pos.bottomLeftGoalPost][Direction::DownRight] -= correction;
    for(int id = m_pos.bottomLeftGoalPost + 1; id < m_pos.bottomRightGoalPost; ++id)
    {
        m_neighbours[id][Direction::DownLeft] -= correction;
        m_neighbours[id][Direction::Down] -= correction;
        m_neighbours[id][Direction::DownRight] -= correction; 
    }
    m_neighbours[m_pos.bottomRightGoalPost][Direction::DownLeft] -= correction;
}

void Field::calculate_neighbours()
{
    calculate_regular_neighbours();
    
    // Fix neighbours that point into score fields.
    // Normal +/- m_width offsets do not work there 
    // because score rows have m_goalWidth vertices, not m_width vertices
    // (since score areas have Direction::None allowed, they are already set correctly)
    fix_goal_area_neighbours();
}