#include "field.hpp"

Field::Field(int width, int height)
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
        m_height = 0;
    else
    {
        std::cout << "height has to be an odd number, at least 3";
        m_height = 7;
        std::cout << "Height was set to 7";
    }

    m_verticesCount = m_width * m_height + 2 * score_area_size;
    allowed.assign(m_verticesCount, 0);
    visited.assign(m_verticesCount, 0);
}

void Field::allowed_init()
{
    const int upperGoalId = 0;
    const int lowerGoalId = m_verticesCount - 1;
    
    allowed[upperGoalId] = NONE;
    allowed[lowerGoalId] = NONE;

    const int topLeftCorner = 1;
    const int topRightCorner = m_width;
    const int bottomLeftCorner = lowerGoalId - m_width;
    const int bottomRightCorner = lowerGoalId - 1;

    allowed[topLeftCorner] = NONE;
    allowed[topRightCorner] = NONE;
    allowed[bottomLeftCorner] = NONE;
    allowed[bottomRightCorner] = NONE;

    //left border without corners
    for(int id = topLeftCorner + m_width; id <= bottomLeftCorner - m_width; id += m_width)
        allowed[id] |= UP_RIGHT | RIGHT | DOWN_RIGHT;

    //right border without corners
    for(int id = topRightCorner + m_width; id <= bottomRightCorner - m_width; id += m_width)
        allowed[id] |= UP_LEFT | LEFT | DOWN_LEFT;

    const int topLeftGoalPost = m_width/2;
    const int topRightGoalPost = topLeftGoalPost + score_area_size + 1;
    const int bottomLeftGoalPost = bottomLeftCorner + m_width/2 - 1;
    const int bottomRightGoalPost = bottomLeftGoalPost + score_area_size + 1;
    
    //upper border without corners
    for(int id = topLeftCorner + 1; id <= topLeftGoalPost; ++id)
        allowed[id] |= DOWN_LEFT | DOWN | DOWN_RIGHT;
    
    allowed[topLeftGoalPost] |= DOWN_LEFT | DOWN | DOWN_RIGHT | RIGHT | UP_RIGHT;
    allowed[topLeftGoalPost + 1] |= UP | RIGHT | DOWN_RIGHT | DOWN | DOWN_LEFT | LEFT;
    allowed[topRightGoalPost] |= UP_LEFT | LEFT | DOWN_LEFT | DOWN | DOWN_RIGHT;

    for(int id = topRightGoalPost + 1; id <= topRightCorner - 1; ++id)
        allowed[id] |= DOWN_LEFT | DOWN | DOWN_RIGHT;
    
    //lower border without corners

    for(int id = bottomLeftCorner + 1; id <= bottomLeftGoalPost - 1; ++id)
        allowed[id] |= UP_LEFT | UP | UP_RIGHT;
    
    allowed[bottomLeftGoalPost] |= UP_LEFT | UP | UP_RIGHT | RIGHT | DOWN_RIGHT;
    allowed[bottomLeftGoalPost + 1] |= UP | UP_RIGHT | RIGHT | DOWN | LEFT | UP_LEFT;
    allowed[bottomRightGoalPost] |= DOWN_LEFT | LEFT | UP_LEFT | UP | UP_RIGHT;

    for(int id = bottomRightGoalPost + 1; id <= bottomRightCorner - 1; ++id)
        allowed[id] |= UP_LEFT | UP | UP_RIGHT;

    //inside
    const int insideTopLeftCorner = topLeftCorner + m_width + 1;
    const int insideTopRightCorner = topRightCorner + m_width - 1;
    const int insideBottomLeftCorner = bottomLeftCorner - m_width + 1;
    const int insideBottomRightCorner = bottomRightCorner - m_width - 1;
    const int insideWidth = m_width - 2;
    const int insideHeight = m_height - 2;

    for(int localY = 0; localY <= insideHeight - 1; ++localY)
    {
        for(int localX = 0; localX <= insideWidth - 1; ++localX)
        {
            allowed[insideTopLeftCorner + localX + m_width * localY] = ALL;
        }
    }
    
    //corners are not allowed
    allowed[insideTopLeftCorner] &= ~UP_LEFT;
    allowed[insideTopRightCorner] &= ~UP_RIGHT;
    allowed[insideBottomLeftCorner] &= ~DOWN_LEFT;
    allowed[insideBottomRightCorner] &= ~DOWN_RIGHT;
}