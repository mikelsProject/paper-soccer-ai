#pragma once

#include <array>
#include <cstdint>
#include <vector>

#include "direction.hpp"

using VertexId = int;

inline constexpr VertexId NoNeighbour = -1;

using VertexNeighbourhood = std::array<VertexId, Direction::Count>;
using Neighbours = std::vector<VertexNeighbourhood>;

using AllowedDirections = std::vector<Direction::Mask>;

using VertexFlag = std::uint8_t;
using VertexFlags = std::vector<VertexFlag>;

#define Log(x) std::cout << #x << ": " << x << std::endl 
