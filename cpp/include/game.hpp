#pragma once

#include <iostream>
#include <optional>
#include <fstream>

#include "direction.hpp"
#include "field.hpp"


class Game
{
public:
    Game(int& width, int& height, int& goalWidth);

    enum class Player : std::uint8_t
    {
        Top = 0,
        Bottom = 1
    };

    struct MoveResult
    {
        bool moved;
        bool gameOver;
        std::optional<Player> winner;
    };

    struct MoveRecord
    {
        VertexId from;
        VertexId to;
        Direction::Value direction;
        Player player;
    };

    void reset_board();
    MoveResult make_move(Direction::Value direction);
    
    Player player_to_move() const;
    VertexId ball_position() const;
    bool is_game_over() const;
    std::optional<Player> winner() const;

    int vertices_count() const;
    int width() const;
    int height() const;
    int goalWidth() const;

    bool is_direction_allowed(VertexId vertex, Direction::Value direction) const;
    bool is_extra_turn_vertex(VertexId vertex) const;

    bool was_visited(int id) const
    {
        for(int i = 0; i < m_path.size(); ++i)
        {
            int visited = m_path[i].from;
            if(visited == id)
                return true;
        }
        return false;
    }


private:
    Field m_field;

    bool m_gameOver;

    AllowedDirections m_allowedDirections;
    VertexFlags m_extraTurnVertices;

    VertexId m_ballPosition;
    Player m_playerToMove;
    std::optional<Player> m_winner;

    std::vector<MoveRecord> m_path;

private:
    void initialize_extra_turn_vertices();
    void remove_allowed_direction(VertexId vertex, Direction::Value direciton);
    bool is_dead_end(VertexId vertex) const;
    bool is_move_legal(Direction::Value direction) const;
    std::optional<Player> check_for_winner(VertexId vertex) const;
    void save_game_state() const;

    static constexpr Player other_player(Player player) {   return player == Player::Top ? Player::Bottom : Player::Top;    }

};