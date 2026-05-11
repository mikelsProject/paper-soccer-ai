#pragma once

#include <iostream>

#include "direction.hpp"
#include "field.hpp"


class Game
{
    Game(int width, int height, int goalWidth);

    // What API functions do we need? ... 
    // What needs to be public and what can be private?
    // move, reset, cancel a move, win detection, loss detection
    // what about GUI? some renderer? SFML?
    // do we to it externally from the game?

    void make_move(Direction::Value direction);


    enum class Player : std::uint8_t
    {
        Top,
        Bottom
    };

private:
    Field m_field;

    AllowedDirections m_allowedDirections;
    VertexFlags m_extraTurnVertices;
    VertexId m_boalPosition;
    Player m_playerToMove;
    std::vector<VertexId> m_path;

private:
    void initialize_extra_turn_vertices();
};