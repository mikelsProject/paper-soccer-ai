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
     m_gameOver(false),
     m_winner(std::nullopt),
     m_allowedDirections(m_field.initial_allowed_directions()),
     m_playerToMove(Player::Top),
     m_ballPosition(m_field.middle_vertex())
{
    initialize_extra_turn_vertices();
    m_path.reserve(m_field.width() * m_field.height());
}

void Game::reset_board()
{
    m_gameOver = false;
    m_winner = std::nullopt;
    m_allowedDirections = m_field.initial_allowed_directions();
    m_playerToMove = Player::Top;
    m_ballPosition = m_field.middle_vertex();
    initialize_extra_turn_vertices();
}

Game::Player Game::player_to_move() const
{
    return m_playerToMove;
}

VertexId Game::ball_position() const
{
    return m_ballPosition;
}

bool Game::is_game_over() const
{
    return m_gameOver;
}

std::optional<Game::Player> Game::winner() const
{
    return m_winner;
}

int Game::vertices_count() const
{
    return m_field.vertices_count();
}

bool Game::is_direction_allowed(VertexId vertex, Direction::Value direction) const
{
    return Direction::contains(m_allowedDirections[vertex], direction);
}

bool Game::is_extra_turn_vertex(VertexId vertex) const
{
    return m_extraTurnVertices[vertex];
}

bool Game::is_dead_end(VertexId vertex) const
{
    return m_allowedDirections[vertex] == Direction::None;
}

bool Game::is_move_legal(Direction::Value direction) const
{
    return Direction::contains(m_allowedDirections[m_ballPosition], direction);
}

std::optional<Game::Player> Game::check_for_winner(VertexId vertex) const
{
    // top goal reached, bottom player won
    if (vertex < m_field.top_goal_vertex() + m_field.goal_width())
        return Player::Bottom;
    
    // bottom goal reached, top player won
    if (vertex >= m_field.bottom_goal_vertex())
        return Player::Top;

    return std::nullopt;
}

void Game::save_game_state() const
{
    std::ofstream state("gamestate.txt");

    //player
    state << static_cast<int>(m_playerToMove) << "\n";

    //ball posiiton flag
    for(int i = 0; i < m_ballPosition; ++i)
        state << "0 ";
    state << "1 ";
    for(int i = m_ballPosition + 1; i < vertices_count(); ++i)
        state << "0 ";
    state << "\n";

    //allowed direction
    for(int i = 0; i < vertices_count(); ++i)
    {
        for(int bit = 0; bit < 8; ++bit)
        {
            state << ((m_allowedDirections[i] >> bit) & 1) << ' ';
        }
    }
    state << "\n";

    //extra turn
    for(int i = 0; i < vertices_count(); ++i)
    {
        state << static_cast<int>(m_extraTurnVertices[i]) << ' ';
    }
}

void Game::remove_allowed_direction(VertexId vertex, Direction::Value direction)
{
    Direction::disable(m_allowedDirections[vertex], direction);
}


Game::MoveResult Game::make_move(Direction::Value direction)
{
    constexpr bool MoveMade = true;
    constexpr bool MoveNotMade = false;

    if(m_gameOver)
        return { MoveNotMade, m_gameOver, m_winner};

    if( is_dead_end(m_ballPosition))
    {   
        m_gameOver = true;
        m_winner = other_player(m_playerToMove);
        return { MoveNotMade, m_gameOver, m_winner };
    }

    if( !is_move_legal(direction))
        return { MoveNotMade, m_gameOver, m_winner };
    

    const VertexId from = m_ballPosition;
    const VertexId to = m_field.neighbour_at(from, direction);

    remove_allowed_direction(from, direction);
    remove_allowed_direction(to, Direction::opposite(direction));

    m_ballPosition = to;
    m_path.push_back({from, to, direction, m_playerToMove});
    
    m_winner = check_for_winner(m_ballPosition);
    if(m_winner.has_value())
    {
        m_gameOver = true;
        save_game_state();
        return {MoveMade, m_gameOver, m_winner};
    }

    // If a player moves the ball into a dead end - that player loses
    // Therefore this check must happen before switching m_playerToMove
    if(is_dead_end(m_ballPosition))
    {
        m_gameOver = true;
        m_winner = other_player(m_playerToMove);
        save_game_state();
        return { MoveMade, m_gameOver, m_winner };
    }
    

    if(!m_extraTurnVertices[m_ballPosition])
        m_playerToMove = other_player(m_playerToMove);

    m_extraTurnVertices[m_ballPosition] = true;

    save_game_state();
    return {MoveMade, m_gameOver, m_winner};
}