#pragma once

#include <iostream>

#include "direction.hpp"
#include "field.hpp"


class Game
{

private:
    Field m_field;

    AllowedDirections m_allowedDirections;
    VertexFlags m_extraTurnVertices;
    VertexId m_boalPosition;
    std::vector<VertexId> m_path;
    // currentPlayer -> upper/lower or first/second
};