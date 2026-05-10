#pragma once

#include <iostream>

#include "direction.hpp"
#include "field.hpp"


class Game
{
    Game(int width, int height, int goalWidth);

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
};