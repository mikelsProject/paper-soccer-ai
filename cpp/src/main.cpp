#include <iostream>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <bitset>
#include "game.hpp"


void print_board(const Game& soccer, int width, int height, int goalWidth)
{
    for(int i = 0; i < height; ++i)
    {
        for(int j = 0; j < width; ++j)
        {
            int id = i*width + j + goalWidth;
            if(id == soccer.ball_position())
                std::cout << "BAL ";
            else
            {
                if(id < 10)
                    std::cout << " ";
                if(id < 100)
                    std::cout << " ";
                std::cout << id << " ";
            }
        }
        std::cout << std::endl;
    }
}


int main()
{
    int width =  11;
    int height = 13;
    int goalWidth = 5;

    Game soccer(width, height, goalWidth);

    int move;
    do
    {
        print_board(soccer, width, height, goalWidth);
        std::cin >> move;
        soccer.make_move(static_cast<Direction::Value>(move));
    } while (!soccer.is_game_over());
    

    std::cout << "compiled\n";
    return 0;
}