#pragma once
#include <cstdint>

enum Direction : uint8_t {
    NONE       = 0,        // 00000000
    UP         = 1 << 0,   // 00000001
    UP_RIGHT   = 1 << 1,   // 00000010
    RIGHT      = 1 << 2,   // 00000100
    DOWN_RIGHT = 1 << 3,   // 00001000
    DOWN       = 1 << 4,   // 00010000
    DOWN_LEFT  = 1 << 5,   // 00100000
    LEFT       = 1 << 6,   // 01000000
    UP_LEFT    = 1 << 7,   // 10000000
    ALL        = 255       // 11111111
};
