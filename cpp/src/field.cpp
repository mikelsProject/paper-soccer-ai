#include "include/field.hpp"

#include <cassert>

int Field::validated_width(int width)
{
    if(width >= 5 && width % 2 == 1)
        return width;

    std::cout << "width has to be an odd number, at least 5\n";
    std::cout << "width was set to default 9\n";
    return 9;
}

int Field::validated_height(int height)
{
    if(height >= 3 && height % 2 == 1)
        return height;

    std::cout << "height has to be an odd number, at least 3";
    std::cout << "height was set to default 13";
    return 13;
}

int Field::validated_goal_width(int goalWidth, int validWidth)
{
    if(goalWidth >= 3 && goalWidth <= validWidth - 2 && goalWidth % 2 == 1)
        return goalWidth;
    
    std::cout << "goal width has to be an odd number, at least 3, smaller than width of the whole field";
    std::cout << "goal width was set to defualt 3";
    return 3;
}

Field::Positions Field::calculate_positions(int width, int height, int goalWidth, int verticesCount)
{
    Positions pos{};
    //beginning of top goal (left side)
    pos.topGoalId = 0;
    //beginning of bottom goal (left side)
    pos.bottomGoalId = verticesCount - goalWidth; 
    
    //field corners
    pos.topLeftCorner = goalWidth;
    pos.topRightCorner = goalWidth + width - 1;
    pos.bottomLeftCorner = goalWidth + width * (height - 1);
    pos.bottomRightCorner = goalWidth + width * height - 1;

    //goals posts
    pos.topLeftGoalPost = goalWidth + (width - goalWidth) / 2;
    pos.topRightGoalPost = pos.topLeftGoalPost + goalWidth - 1;
    pos.bottomLeftGoalPost = pos.bottomLeftCorner + (width - goalWidth) / 2;
    pos.bottomRightGoalPost = pos.bottomLeftGoalPost + goalWidth - 1;

    //corners of the field part without borders
    pos.insideTopLeftCorner = pos.topLeftCorner + width + 1;
    pos.insideTopRightCorner = pos.topRightCorner + width - 1;
    pos.insideBottomLeftCorner = pos.bottomLeftCorner - width + 1;
    pos.insideBottomRightCorner = pos.bottomRightCorner - width - 1;

    pos.fieldMiddle = (goalWidth - 1)/2 + width * (height + 1)/2;

    return pos;
}


Field::Field(int width, int height, int goalWidth)
    :m_width(validated_width(width)), 
     m_height(validated_height(height)),
     m_goalWidth(validated_goal_width(goalWidth, m_width)),
     m_verticesCount(m_width * m_height + 2 * goalWidth),
     m_pos(calculate_positions(m_width, m_height, m_goalWidth, m_verticesCount))
{
    initialize_allowed_directions();
    calculate_border();
}

int Field::width() const
{
    return m_width;
}

int Field::height() const
{
    return m_height;
}

int Field::goal_width() const
{
    return m_goalWidth;
}

int Field::vertices_count() const
{
    return m_verticesCount;
}

const AllowedDirections& Field::initial_allowed_directions() const
{
    return m_initialAllowedDirections;
}

const VertexFlags& Field::border_flags() const
{
    return m_borderFlags;
}

VertexId Field::middle_vertex() const
{
    return m_pos.fieldMiddle;
}

VertexId Field::top_goal_vertex() const
{
    return m_pos.topGoalId;
}

VertexId Field::bottom_goal_vertex() const
{
    return m_pos.bottomGoalId;
}

VertexId Field::top_left_corner() const
{
    return m_pos.topLeftCorner;
}

VertexId Field::top_right_corner() const
{
    return m_pos.topRightCorner;
}

VertexId Field::bottom_left_corner() const
{
    return m_pos.bottomLeftCorner;
}

VertexId Field::bottom_right_corner() const
{
    return m_pos.bottomRightCorner;
}

VertexId Field::neighbour_at(VertexId id, Direction::Value direction) const
{
    assert(id >= 0);
    assert(id < m_verticesCount);
    assert(static_cast<std::size_t>(direction) < Direction::Count);

    return m_neighbours[id][direction];
}

bool Field::is_initial_direction_allowed(VertexId id , Direction::Value direction) const
{
    return Direction::contains(m_initialAllowedDirections[id], direction);
}


void Field::initialize_allowed_directions_vertical_borders()
{
    namespace Dir = Direction;
    //left border without corners
    for(VertexId id = m_pos.topLeftCorner + m_width; id <= m_pos.bottomLeftCorner - m_width; id += m_width)
        m_initialAllowedDirections[id] |= Dir::UpRightMask | Dir::RightMask | Dir::DownRightMask;

    //right border without corners
    for(VertexId id = m_pos.topRightCorner + m_width; id <= m_pos.bottomRightCorner - m_width; id += m_width)
        m_initialAllowedDirections[id] |= Dir::UpLeftMask | Dir::LeftMask | Dir::DownLeftMask;
}

void Field::initialize_allowed_directions_top_border()
{
    namespace Dir = Direction;
    //top border without corners
    
    for(VertexId id = m_pos.topLeftCorner + 1; id < m_pos.topLeftGoalPost; ++id)
        m_initialAllowedDirections[id] |= Dir::DownLeftMask | Dir::DownMask | Dir::DownRightMask;
    
        //goal area
    m_initialAllowedDirections[m_pos.topLeftGoalPost] |= Dir::DownLeftMask | Dir::DownMask | Dir::DownRightMask | Dir::RightMask | Dir::UpRightMask;

    for(VertexId id = m_pos.topLeftGoalPost + 1; id < m_pos.topRightGoalPost; ++id)
        m_initialAllowedDirections[id] |= Dir::All;

    m_initialAllowedDirections[m_pos.topRightGoalPost] |= Dir::UpLeftMask | Dir::LeftMask | Dir::DownLeftMask | Dir::DownMask | Dir::DownRightMask;
        //

    for(VertexId id = m_pos.topRightGoalPost + 1; id < m_pos.topRightCorner; ++id)
        m_initialAllowedDirections[id] |= Dir::DownLeftMask | Dir::DownMask | Dir::DownRightMask;
    
}

void Field::initialize_allowed_directions_bottom_border()
{
    namespace Dir = Direction;
    //bottom border without corners

    for(VertexId id = m_pos.bottomLeftCorner + 1; id < m_pos.bottomLeftGoalPost; ++id)
        m_initialAllowedDirections[id] |= Dir::UpLeftMask | Dir::UpMask | Dir::UpRightMask;
    
        //goal area
    m_initialAllowedDirections[m_pos.bottomLeftGoalPost] |= Dir::UpLeftMask | Dir::UpMask | Dir::UpRightMask | Dir::RightMask | Dir::DownRightMask;

    for(VertexId id = m_pos.bottomLeftGoalPost + 1; id < m_pos.bottomRightGoalPost; ++id)
        m_initialAllowedDirections[id] |= Dir::All;

    m_initialAllowedDirections[m_pos.bottomRightGoalPost] |= Dir::DownLeftMask | Dir::LeftMask | Dir::UpLeftMask | Dir::UpMask | Dir::UpRightMask;
        //

    for(VertexId id = m_pos.bottomRightGoalPost + 1; id <= m_pos.bottomRightCorner - 1; ++id)
        m_initialAllowedDirections[id] |= Dir::UpLeftMask | Dir::UpMask | Dir::UpRightMask;

}

void Field::initialize_allowed_directions_inside()
{
    namespace Dir = Direction;

    const int insideWidth = m_width - 2;
    const int insideHeight = m_height - 2;

    for(int localY = 0; localY < insideHeight; ++localY)
    {
        for(int localX = 0; localX < insideWidth; ++localX)
        {
            m_initialAllowedDirections[m_pos.insideTopLeftCorner + localX + m_width * localY] = Dir::All;
        }
    }
    
        //but corners of the field are not allowed to be moved into
    m_initialAllowedDirections[m_pos.insideTopLeftCorner] &= ~Dir::UpLeftMask;
    m_initialAllowedDirections[m_pos.insideTopRightCorner] &= ~Dir::UpRightMask;
    m_initialAllowedDirections[m_pos.insideBottomLeftCorner] &= ~Dir::DownLeftMask;
    m_initialAllowedDirections[m_pos.insideBottomRightCorner] &= ~Dir::DownRightMask;
}

void Field::initialize_allowed_directions()
{
    m_initialAllowedDirections.assign(m_verticesCount, Direction::None);
    
    // Corners and score fields remain set to Direction::None intentionally.
    // The code below only adds directions to playable border/interior fields.

    initialize_allowed_directions_vertical_borders();
    initialize_allowed_directions_top_border();
    initialize_allowed_directions_bottom_border();
    initialize_allowed_directions_inside();
}


void Field::calculate_border()
{
    m_borderFlags.assign(m_verticesCount, false);

    //top border with score area
    for(VertexId id = m_pos.topGoalId; id < m_pos.topGoalId + m_goalWidth; ++id)
        m_borderFlags[id] = true;

    for(VertexId id = m_pos.topLeftCorner; id <= m_pos.topLeftGoalPost; ++id)
        m_borderFlags[id] = true;
    
    for(VertexId id = m_pos.topRightGoalPost; id <= m_pos.topRightCorner; ++id)
        m_borderFlags[id] = true;
    
    //left border
    for(VertexId id = m_pos.topLeftCorner; id <= m_pos.bottomLeftCorner; id += m_width)
        m_borderFlags[id] = true;

    //right border
    for(VertexId id = m_pos.topRightCorner; id <= m_pos.bottomRightCorner; id += m_width)
        m_borderFlags[id] = true;

    //bottom border with score area
    for(VertexId id = m_pos.bottomGoalId; id < m_pos.bottomGoalId + m_goalWidth; ++id)
        m_borderFlags[id] = true;

    for(VertexId id = m_pos.bottomLeftCorner; id <= m_pos.bottomLeftGoalPost; ++id)
        m_borderFlags[id] = true;

    for(VertexId id = m_pos.bottomRightGoalPost; id <= m_pos.bottomRightCorner; ++id)
        m_borderFlags[id] = true;
}


void Field::calculate_regular_neighbours()
{
    const std::array<int, Direction::Count> directionOffset = 
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

    for(VertexId id = 0; id < m_verticesCount; ++id)
    {   
        for(Direction::Value direction : Direction::Values)
        {
            if(is_initial_direction_allowed(id, direction))
                m_neighbours[id][direction] =  id + directionOffset[direction];
            else
                m_neighbours[id][direction] = NoNeighbour;
        }      
    }
}

void Field::fix_goal_area_neighbours()
{
    const int correction = (m_width - m_goalWidth) / 2;
    
    //top are near goal
    m_neighbours[m_pos.topLeftGoalPost][Direction::UpRight] += correction;
    for(VertexId id = m_pos.topLeftGoalPost + 1; id < m_pos.topRightGoalPost; ++id)
    {  
        m_neighbours[id][Direction::Up] += correction;
        m_neighbours[id][Direction::UpRight] += correction;
        m_neighbours[id][Direction::UpLeft] += correction;
    }
    m_neighbours[m_pos.topRightGoalPost][Direction::UpLeft] += correction; 

    //bottom area near goal
    m_neighbours[m_pos.bottomLeftGoalPost][Direction::DownRight] -= correction;
    for(VertexId id = m_pos.bottomLeftGoalPost + 1; id < m_pos.bottomRightGoalPost; ++id)
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