#include "game.hpp"

void Game::initialize_extra_turn_vertices()
{
    m_extraTurnVertices = m_field.border_flags();

    //middle vertex is the starting point, so it's visited - therefore extra turn
    m_extraTurnVertices[m_field.middle_vertex()] = true;

    // score areas should not be extra turn vertices, so they need to be turned off
    const VertexId topGoal = m_field.top_goal_vertex();
    const VertexId bottomGoal = m_field.bottom_goal_vertex();
    const int goalWidth = m_field.goal_width();

    for(VertexId id = topGoal; id < topGoal + goalWidth; ++id)
        m_extraTurnVertices[id] = false;

    for(VertexId id = bottomGoal; id < bottomGoal + goalWidth; ++id)
        m_extraTurnVertices[id] = false;

    // same for the corners
    m_extraTurnVertices[m_field.top_left_corner()] = false;
    m_extraTurnVertices[m_field.top_right_corner()] = false;
    m_extraTurnVertices[m_field.bottom_left_corner()] = false;
    m_extraTurnVertices[m_field.bottom_right_corner()] = false;
}


Game::Game(int width, int height, int goalWidth)
    :m_field(width, height, goalWidth),
     m_allowedDirections(m_field.initial_allowed_directions()),
     m_playerToMove(Player::Top),
     m_ballPosition(m_field.middle_vertex())
{
    initialize_extra_turn_vertices();
}

bool Game::is_move_legal(Direction::Value direction)
{
    return Direction::contains(m_allowedDirections[m_ballPosition], direction);
}

void Game::remove_allowed_direction(VertexId vertex, Direction::Value direction)
{
    Direction::disable(m_allowedDirections[vertex], direction);
}


bool Game::make_move(Direction::Value direction)
{
    if(!is_move_legal(direction))
        return false;
    
    const VertexId from = m_ballPosition;
    const VertexId to = m_field.neighbour_at(from, direction);

    remove_allowed_direction(from, direction);
    remove_allowed_direction(to, direction);

    m_ballPosition = to;

    m_path.push_back(m_ballPosition);

    if(!m_extraTurnVertices[m_ballPosition])
        m_playerToMove = other_player(m_playerToMove);

    m_extraTurnVertices[m_ballPosition] = true;
}