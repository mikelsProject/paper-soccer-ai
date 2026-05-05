#include <iostream>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <bitset>


enum Direction : uint8_t {
    NONE       = 0,      // 00000000
    UP         = 1 << 0, // 00000001
    UP_RIGHT   = 1 << 1, // 00000010
    RIGHT      = 1 << 2, // 00000100
    DOWN_RIGHT = 1 << 3, // 00001000
    DOWN       = 1 << 4, // 00010000
    DOWN_LEFT  = 1 << 5, // 00100000
    LEFT       = 1 << 6, // 01000000
    UP_LEFT    = 1 << 7, // 10000000
    ALL        = 255     // 11111111
};

class Field
{
public:
    const int score_area_size = 1;

    Field(int width, int height);

private:
    int m_width;
    int m_height;
    int m_verticesCount;
    std::vector<uint8_t> allowed; //directions in which we can still move
    std::vector<uint8_t> visited; //Verticies which were already visited 0 - not visited, 1 - visited
    std::vector<int> path;

private:
    void allowed_init();
    void visited_init();
};