#pragma once
#include <cstdint>

namespace Direction
{
    const int count = 8;

    enum Index
    {
        Up        = 0,
        UpRight   = 1,
        Right     = 2,
        DownRight = 3,
        Down      = 4,
        DownLeft  = 5,
        Left      = 6,
        UpLeft    = 7
    };

    enum Mask : std::uint8_t {
        None       = 0,                 // 00000000
        UpMask         = 1 << Up,       // 00000001
        UpRightMask   = 1 << UpRight,   // 00000010
        RightMask      = 1 << Right,    // 00000100
        DownRightMask = 1 << DownRight, // 00001000
        DownMask       = 1 << Down,     // 00010000
        DownLeftMask  = 1 << DownLeft,  // 00100000
        LeftMask       = 1 << Left,     // 01000000
        UpLeftMask    = 1 << UpLeft,    // 10000000
        All        = 255                // 11111111
    };
}