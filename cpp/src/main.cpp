#include <iostream>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <bitset>
#include "game.hpp"

namespace Color
{
    constexpr const char* reset  = "\033[0m";
    constexpr const char* red    = "\033[31m";
    constexpr const char* green  = "\033[32m";
    constexpr const char* yellow = "\033[33m";
    constexpr const char* blue   = "\033[34m";
}

void print_board(const Game& soccer, int width, int height, int goalWidth)
{
    for(int i = 0; i < height; ++i)
    {
        for(int j = 0; j < width; ++j)
        {
            int id = i*width + j + goalWidth;
            
            if(id == soccer.ball_position())
            {
                if(soccer.player_to_move() == Game::Player::Top)
                    std::cout << Color::green;
                else
                    std::cout << Color::red;
                std::cout << "BAL ";
                std::cout << Color::reset;
            }
            else
            {
                if(soccer.was_visited(id))
                    std::cout << Color::blue;
                if(id < 10)
                    std::cout << " ";
                if(id < 100)
                    std::cout << " ";
                std::cout << id << " ";
                std::cout << Color::reset;
            }
        }
        std::cout << std::endl;
    }
}

Direction::Value move_from_keyboard_num(int move)
{
    switch(move)
    {
        case 8:
            return Direction::Up;
        case 9:
            return Direction::UpRight;
        case 6:
            return Direction::Right;
        case 3: 
            return Direction::DownRight;
        case 2:
            return Direction::Down;
        case 1:
            return Direction::DownLeft;
        case 4:
            return Direction::Left;
        case 7: 
            return Direction::UpLeft;
        default:
            return static_cast<Direction::Value>(0);
    }
}

int main()
{
    int width =  11;
    int height = 13;
    int goalWidth = 3;

    Game soccer(width, height, goalWidth);
    int move;
    do
    {
        print_board(soccer, width, height, goalWidth);
        std::cin >> move;
        soccer.make_move(move_from_keyboard_num(move));
        //soccer.make_move(static_cast<Direction::Value>(move));
    } while (!soccer.is_game_over());
    

    std::cout << "Game Over!\n";
    if(soccer.winner().value() == Game::Player::Top)
        std::cout << "Top player won\n";
    else
        std::cout << "Bottom player won\n";
    return 0;
}