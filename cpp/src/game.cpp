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
     m_boalPosition(m_field.middle_vertex())
{
    initialize_extra_turn_vertices();
}

void Game::make_move(Direction::Value Direction)
{
    // check if move is legal now - using allowed
    // make the move - update ballPosition
    // add move to path
    // based on extraTurn vertices change the current player (or not)
    // modify extra turn vertices
    // modify allowed directions, removing the used edge from both
    // vertices of allowedDirection

    // game_class branch test
}