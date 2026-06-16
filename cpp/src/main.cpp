#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <thread>

#include "game.hpp"

namespace Color {
constexpr const char* Reset = "\033[0m";
constexpr const char* Red = "\033[31m";
constexpr const char* Green = "\033[32m";
constexpr const char* Blue = "\033[34m";
}

void print_board(const Game& soccer, int width, int height, int goalWidth)
{
    std::cout << "\n";

    for (int i = 0; i < height; ++i) {
        for (int j = 0; j < width; ++j) {
            int id = i * width + j + goalWidth;

            if (id == soccer.ball_position()) {
                if (soccer.player_to_move() == Game::Player::Top)
                    std::cout << Color::Green;
                else
                    std::cout << Color::Red;

                std::cout << "BAL ";
                std::cout << Color::Reset;
            } else {
                if (soccer.was_visited(id))
                    std::cout << Color::Blue;

                if (id < 10)
                    std::cout << " ";
                if (id < 100)
                    std::cout << " ";

                std::cout << id << " ";
                std::cout << Color::Reset;
            }
        }

        std::cout << "\n";
    }

    std::cout << "\n";
}

std::string player_name(Game::Player player)
{
    if (player == Game::Player::Top)
        return "Top";

    return "Bottom";
}

std::string direction_name(Direction::Value direction)
{
    switch (direction) {
    case Direction::Up:
        return "up";
    case Direction::UpRight:
        return "up-right";
    case Direction::Right:
        return "right";
    case Direction::DownRight:
        return "down-right";
    case Direction::Down:
        return "down";
    case Direction::DownLeft:
        return "down-left";
    case Direction::Left:
        return "left";
    case Direction::UpLeft:
        return "up-left";
    default:
        return "invalid";
    }
}

Direction::Value move_from_keyboard_num(int move)
{
    switch (move) {
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
        return static_cast<Direction::Value>(255);
    }
}

bool is_valid_direction(Direction::Value direction)
{
    return direction == Direction::Up || direction == Direction::UpRight || direction == Direction::Right || direction == Direction::DownRight || direction == Direction::Down
        || direction == Direction::DownLeft || direction == Direction::Left || direction == Direction::UpLeft;
}

void print_controls()
{
    std::cout << "7 8 9\n";
    std::cout << "4   6\n";
    std::cout << "1 2 3\n\n";
}

int read_ai_move()
{
    std::ifstream file("move.txt");

    int move = -1;
    file >> move;

    return move;
}

std::string choose_bot_mode()
{
    std::cout << "\nChoose mode:\n";
    std::cout << "1 - heuristic\n";
    std::cout << "2 - search\n";
    std::cout << "3 - neural\n";
    std::cout << "Your choice: ";

    int choice;
    std::cin >> choice;

    if (choice == 1)
        return "heuristic";

    if (choice == 2)
        return "search";

    return "neural";
}

bool run_python_bot(const std::string& botMode, int maxDepth, double timeLimit)
{
    std::ostringstream command;

#ifdef _WIN32
    command << "\"..\\.venv\\Scripts\\python.exe\" \"..\\python\\play.py\" " << botMode;
#else
    command << "\"../../.venv/bin/python\" \"../python/play.py\" " << botMode;
#endif

    if (botMode == "search") {
        command << " " << maxDepth << " " << timeLimit;
    }

    command << " > bot_log.txt 2>&1";

    int result = std::system(command.str().c_str());

    return result == 0;
}

void write_web_status(const std::string& status)
{
    std::ofstream file("web_status.txt");
    file << status;
}

int wait_for_web_move()
{
    while (true) {
        std::ifstream file("web_move.txt");

        int move = -1;
        file >> move;

        if (move >= 0) {
            file.close();
            std::remove("web_move.txt");
            return move;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

void play_web(Game& soccer, Game::Player humanPlayer, const std::string& botMode, int maxDepth, double timeLimit)
{
    std::remove("web_move.txt");
    std::remove("move.txt");

    while (!soccer.is_game_over()) {
        if (soccer.player_to_move() == humanPlayer) {
            write_web_status("human");

            int move = wait_for_web_move();
            Direction::Value direction = static_cast<Direction::Value>(move);

            if (!is_valid_direction(direction))
                continue;

            Game::MoveResult result = soccer.make_move(direction);

            if (!result.moved)
                continue;
        } else {
            write_web_status("bot");

            if (!run_python_bot(botMode, maxDepth, timeLimit)) {
                write_web_status("bot_failed");
                std::cout << "Bot failed\n";
                return;
            }

            int aiMove = read_ai_move();
            Direction::Value direction = static_cast<Direction::Value>(aiMove);

            if (!is_valid_direction(direction)) {
                write_web_status("invalid_bot_move");
                std::cout << "Invalid bot move\n";
                return;
            }

            Game::MoveResult result = soccer.make_move(direction);

            if (!result.moved) {
                write_web_status("illegal_bot_move");
                std::cout << "Illegal bot move\n";
                return;
            }
        }
    }

    if (soccer.winner().has_value()) {
        write_web_status("gameover_" + player_name(soccer.winner().value()));
    } else {
        write_web_status("gameover");
    }
}

int main(int argc, char* argv[])
{
    int width = 11;
    int height = 13;
    int goalWidth = 5;

    Game soccer(width, height, goalWidth);

    if (argc > 1 && std::string(argv[1]) == "init") {
        write_web_status("waiting");
        std::cout << "Initial gamestate saved\n";
        return 0;
    }

    if (argc > 1 && std::string(argv[1]) == "web") {
        int side = 1;
        std::string botMode = "search";
        int maxDepth = 8;
        double timeLimit = 2.0;

        if (argc > 2)
            side = std::stoi(argv[2]);

        if (argc > 3)
            botMode = argv[3];

        if (argc > 4)
            maxDepth = std::stoi(argv[4]);

        if (argc > 5)
            timeLimit = std::stod(argv[5]);

        Game::Player humanPlayer = Game::Player::Top;

        if (side == 1)
            humanPlayer = Game::Player::Bottom;

        std::cout << "Paper Soccer AI web game\n";
        std::cout << "Human: " << player_name(humanPlayer) << "\n";
        std::cout << "Bot: " << botMode << "\n";
        std::cout << "Search max depth: " << maxDepth << "\n";
        std::cout << "Search time limit: " << timeLimit << " s\n";

        play_web(soccer, humanPlayer, botMode, maxDepth, timeLimit);
        return 0;
    }

    std::cout << "Paper Soccer AI\n\n";

    print_controls();

    std::cout << "Choose your side:\n";
    std::cout << "0 - Top\n";
    std::cout << "1 - Bottom\n";
    std::cout << "Your choice: ";

    int side;
    std::cin >> side;

    Game::Player humanPlayer = Game::Player::Top;

    if (side == 1)
        humanPlayer = Game::Player::Bottom;

    std::string botMode = choose_bot_mode();
    int maxDepth = 8;
    double timeLimit = 2.0;

    std::cout << "\nYou: " << player_name(humanPlayer) << "\n";
    std::cout << "Bot: " << botMode << "\n";

    while (!soccer.is_game_over()) {
        print_board(soccer, width, height, goalWidth);

        std::cout << "Move: " << player_name(soccer.player_to_move()) << "\n";

        if (soccer.player_to_move() == humanPlayer) {
            int move;
            std::cout << "Your move: ";
            std::cin >> move;

            Direction::Value direction = move_from_keyboard_num(move);

            if (!is_valid_direction(direction)) {
                std::cout << "Invalid move\n";
                continue;
            }

            Game::MoveResult result = soccer.make_move(direction);

            if (!result.moved) {
                std::cout << "Illegal move\n";
                continue;
            }
        } else {
            if (!run_python_bot(botMode, maxDepth, timeLimit)) {
                std::cout << "Bot failed, check the bot_log.txt\n";
                return 1;
            }

            int aiMove = read_ai_move();

            Direction::Value direction = static_cast<Direction::Value>(aiMove);

            if (!is_valid_direction(direction)) {
                std::cout << "Invalid bot move: " << aiMove << "\n";
                return 1;
            }

            Game::MoveResult result = soccer.make_move(direction);

            if (!result.moved) {
                std::cout << "Illegal bot move: " << aiMove << "\n";
                return 1;
            }

            std::cout << "Bot: " << aiMove << " (" << direction_name(direction) << ")\n";
        }
    }

    print_board(soccer, width, height, goalWidth);

    if (soccer.winner().has_value()) {
        std::cout << player_name(soccer.winner().value()) << " won\n";
    }

    return 0;
}