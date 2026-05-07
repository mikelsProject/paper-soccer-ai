#include "include/field.hpp"

Field::Field(int width, int height, int goalWidth)
{
    if(width >= 5 && width % 2 == 1)
        m_width = width;
    else
    {
        std::cout << "width has to be an odd number, at least 5\n";
        m_width = 5;
        std::cout << "width was set to 5\n";
    }

    if(height >= 3 && height % 2 == 1)
        m_height = height;
    else
    {
        std::cout << "height has to be an odd number, at least 3";
        m_height = 7;
        std::cout << "height was set to 7";
    }

    if(goalWidth >= 3 && goalWidth <= width - 2 && goalWidth % 2 == 1)
        m_goalWidth = goalWidth;
    else
    {
        std::cout << "goal width has to be an odd number, at least 3, smaller than width of the whole field";
        m_goalWidth = 3;
        std::cout << "goal width was set to 3";
    }

    m_verticesCount = m_width * m_height + 2 * goalWidth;
    allowed_init();
    visited_init();
}

void Field::allowed_init()
{
    m_allowed.assign(m_verticesCount, NONE);

    const int upperGoalId = 0;  //beginning of upper goal (left side)
    const int lowerGoalId = m_verticesCount - (m_goalWidth - 1); //beginning of lower goal (left side)
    
    //can't move anywhere after scoring a goal
    for(int id = upperGoalId; id < m_goalWidth; ++id)
        m_allowed[id] = NONE;
    for(int id = lowerGoalId; id < lowerGoalId + m_goalWidth; ++id)
        m_allowed[id] = NONE;

    
    const int topLeftCorner = m_goalWidth;
    const int topRightCorner = m_goalWidth + m_width - 1;
    const int bottomLeftCorner = m_goalWidth + m_width * (m_height - 1);
    const int bottomRightCorner = m_goalWidth + m_width * m_height - 1;

    m_allowed[topLeftCorner] = NONE;
    m_allowed[topRightCorner] = NONE;
    m_allowed[bottomLeftCorner] = NONE;
    m_allowed[bottomRightCorner] = NONE;

    //left border without corners
    for(int id = topLeftCorner + m_width; id <= bottomLeftCorner - m_width; id += m_width)
        m_allowed[id] |= UP_RIGHT | RIGHT | DOWN_RIGHT;

    //right border without corners
    for(int id = topRightCorner + m_width; id <= bottomRightCorner - m_width; id += m_width)
        m_allowed[id] |= UP_LEFT | LEFT | DOWN_LEFT;

    const int topLeftGoalPost = m_goalWidth + (m_width - m_goalWidth) / 2;
    const int topRightGoalPost = topLeftGoalPost + m_goalWidth - 1;
    const int bottomLeftGoalPost = bottomLeftCorner + (m_width - m_goalWidth) / 2;
    const int bottomRightGoalPost = bottomLeftGoalPost + m_goalWidth - 1;


    //upper border without corners
    for(int id = topLeftCorner + 1; id < topLeftGoalPost; ++id)
        m_allowed[id] |= DOWN_LEFT | DOWN | DOWN_RIGHT;
    
        //goal area
    m_allowed[topLeftGoalPost] |= DOWN_LEFT | DOWN | DOWN_RIGHT | RIGHT | UP_RIGHT;

    for(int id = topLeftGoalPost + 1; id < topRightGoalPost; ++id)
        m_allowed[id] |= ALL;

    m_allowed[topRightGoalPost] |= UP_LEFT | LEFT | DOWN_LEFT | DOWN | DOWN_RIGHT;
        //

    for(int id = topRightGoalPost + 1; id < topRightCorner; ++id)
        m_allowed[id] |= DOWN_LEFT | DOWN | DOWN_RIGHT;
    
    //lower border without corners
    for(int id = bottomLeftCorner + 1; id < bottomLeftGoalPost; ++id)
        m_allowed[id] |= UP_LEFT | UP | UP_RIGHT;
    
        //goal area
    m_allowed[bottomLeftGoalPost] |= UP_LEFT | UP | UP_RIGHT | RIGHT | DOWN_RIGHT;

    for(int id = bottomLeftGoalPost + 1; id < bottomRightGoalPost; ++id)
        m_allowed[id] |= ALL;

    m_allowed[bottomRightGoalPost] |= DOWN_LEFT | LEFT | UP_LEFT | UP | UP_RIGHT;
        //

    for(int id = bottomRightGoalPost + 1; id <= bottomRightCorner - 1; ++id)
        m_allowed[id] |= UP_LEFT | UP | UP_RIGHT;

    //inside
    const int insideTopLeftCorner = topLeftCorner + m_width + 1;
    const int insideTopRightCorner = topRightCorner + m_width - 1;
    const int insideBottomLeftCorner = bottomLeftCorner - m_width + 1;
    const int insideBottomRightCorner = bottomRightCorner - m_width - 1;
    const int insideWidth = m_width - 2;
    const int insideHeight = m_height - 2;

    for(int localY = 0; localY < insideHeight; ++localY)
    {
        for(int localX = 0; localX < insideWidth; ++localX)
        {
            m_allowed[insideTopLeftCorner + localX + m_width * localY] = ALL;
        }
    }
    
        //but corners of the field are not allowed
    m_allowed[insideTopLeftCorner] &= ~UP_LEFT;
    m_allowed[insideTopRightCorner] &= ~UP_RIGHT;
    m_allowed[insideBottomLeftCorner] &= ~DOWN_LEFT;
    m_allowed[insideBottomRightCorner] &= ~DOWN_RIGHT;
}

void Field::visited_init()
{
    m_visited.assign(m_verticesCount, NOT_VISITED);
    const int fieldMiddle = (m_goalWidth - 1)/2 + m_width * (m_height + 1)/2;
    m_visited[fieldMiddle] = VISITED;   
}

void Field::neighbours_calculate()
{
    std::array<int, DIRECTIONS_COUNT> directionOffset = 
    { 
        -m_width,      // 0 -> UP
        -m_width + 1,  // 1 -> UP_RIGHT
        1,             // 2 -> RIGHT
        m_width + 1,   // 3 -> DOWN_RIGHT
        m_width,       // 4 -> DOWN
        m_width - 1,   // 5 -> DOWN_LEFT
        -1,            // 6 -> LEFT
        -m_width - 1   // 7 -> UP_LEFT
    };

    for(int id = 0; id < m_verticesCount; ++id)
    {   
        for(int direction = 0; direction < DIRECTIONS_COUNT; ++direction)
        {
            //is the bit for current direction set to 1 (allowed)
            bool directonAllowed = m_allowed[id] & (1u << direction);
            if(directonAllowed)
            {
                m_neighbours[id][direction] =  id + directionOffset[direction];
            }
            else
            {
                m_neighbours[id][direction] = NO_NEIGHBOUR;
            }
        }      
    }

    //fix edge cases - neighbours of goals (since goals have NONE allowed, so they are set correctly)

    for(int id = ; id < m_goalWidth; ++id)
    {  
        for(int direction = 0; direction < DIRECTIONS_COUNT; ++direction)
        m_neighbours[id][direction] = NO_NEIGHBOUR;
    }


}