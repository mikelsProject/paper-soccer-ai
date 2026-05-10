#pragma once

#include <array>
#include <cstdint>
#include <vector>

#include "direction.hpp"

using VertexId = int;

inline constexpr VertexId NoNeighbour = -1;

using DirectionMask = std::uint8_t;

using VertexNeighbourhood = std::array<VertexId, Direction::Count>;
using Neighbours = std::vector<VertexNeighbourhood>;

using AllowedDirections = std::vector<DirectionMask>;

using VertexFlag = std::uint8_t;
using VertexFlags = std::vector<VertexFlag>;
