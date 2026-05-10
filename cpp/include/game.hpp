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
    
    // what game needs to know - the full game state?
    // extraTurnVertices
    // allowedDirections
    // currentPlayer -> upper/lower or first/second
    // we can keep track of the path too, not neccessary for the gameplay probably
    // 
    // what info will we take from Field, check in field?
    // probably not allowedDirections, because it has to be updated and field is kind of the raw state
    // what about neighbours? they stay the same... altough they kind of could change to NoNeighbour, once we moved
    // so maybe we should keep this thing here too, not to confuse the Neural network with impossible neighbours
    // 
    // no - neighbours is a geometry things, of exisitng edges, so
    // not stored in game, not modified
};