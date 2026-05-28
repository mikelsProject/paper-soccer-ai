#pragma once

#include <cstdint>
#include <array>

namespace Direction
{
    inline constexpr std::size_t Count = 8;
    
    enum Value : std::uint8_t
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

    inline constexpr std::array<Value, Count> Values
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


    using Mask = std::uint8_t;

    inline constexpr Mask None          = 0;               // 00000000            
    inline constexpr Mask UpMask        = 1u << Up;        // 00000001     
    inline constexpr Mask UpRightMask   = 1u << UpRight;   // 00000010             
    inline constexpr Mask RightMask     = 1u << Right;     // 00000100         
    inline constexpr Mask DownRightMask = 1u << DownRight; // 00001000             
    inline constexpr Mask DownMask      = 1u << Down;      // 00010000         
    inline constexpr Mask DownLeftMask  = 1u << DownLeft;  // 00100000             
    inline constexpr Mask LeftMask      = 1u << Left;      // 01000000         
    inline constexpr Mask UpLeftMask    = 1u << UpLeft;    // 10000000         
    inline constexpr Mask All           = 0xFF;            // 11111111 


    constexpr Mask mask_from_value(Value direction)
    {
        return static_cast<Mask>(1u << direction);
    }

    inline constexpr std::array<Value, Count> Opposites
    {
        Down,       // Up
        DownLeft,   // UpRight
        Left,       // Right 
        UpLeft,     // DownRight
        Up,         // Down
        UpRight,    // DownLeft
        Right,      // Left
        DownRight   // UpLeft
    };

    constexpr Value opposite(Value direction)
    {
        return Opposites[direction];
    }

    constexpr bool contains(Mask mask, Value direction)
    {
        return (mask & mask_from_value(direction)) != None;
    }

    inline void enable(Mask& mask, Value direction)
    {
        mask |= mask_from_value(direction);
    }

    inline void enable(Mask& mask, Mask directions)
    {
        mask |= directions;
    }

    inline void disable(Mask& mask, Value direction)
    {
        mask &= ~mask_from_value(direction);
    }

    inline void disable(Mask& mask, Mask directions)
    {
        mask &= ~directions;
    }

}