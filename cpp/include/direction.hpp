#pragma once

#include <cstdint>

namespace Direction
{
    inline constexpr std::size_t Count = 8;

    enum Index : std::int8_t
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

    inline constexpr std::array<Index, Count> Indices
    {
        Up, 
        UpRight,
        Right,
        DownRight,
        Down,
        DownLeft,
        Left,
        UpLeft
    };

    enum Mask : std::uint8_t 
    {
        None           = 0,                 // 00000000
        UpMask         = 1 << Up,           // 00000001
        UpRightMask    = 1 << UpRight,      // 00000010
        RightMask      = 1 << Right,        // 00000100
        DownRightMask  = 1 << DownRight,    // 00001000
        DownMask       = 1 << Down,         // 00010000
        DownLeftMask   = 1 << DownLeft,     // 00100000
        LeftMask       = 1 << Left,         // 01000000
        UpLeftMask     = 1 << UpLeft,       // 10000000
        All        = 0xFF                   // 11111111
    };

    constexpr Mask mask_from_index(Index dir)
    {
        return static_cast<Mask>(1u << dir);
    }
}