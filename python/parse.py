import torch
from dataclasses import dataclass


@dataclass
class GameState:
    player: int
    ball: torch.Tensor
    allowed: torch.Tensor
    extra_turn: torch.Tensor
    neighbours: torch.Tensor

    @property
    def vertices_count(self):
        return self.ball.numel()

    @property
    def current_vertex(self):
        return int(torch.argmax(self.ball).item())

    @property
    def input_size(self):
        return 1 + self.vertices_count + self.vertices_count * 8 + self.vertices_count

    def legal_moves(self):
        return self.allowed[self.current_vertex].bool()

    def to_tensor(self):
        player_tensor = torch.tensor([float(self.player)])

        state = torch.cat([
            player_tensor,
            self.ball.float(),
            self.allowed.flatten().float(),
            self.extra_turn.float()
        ])

        return state.unsqueeze(0)


def read_ints(line):
    return [int(x) for x in line.strip().split()]


def load_game_state(path):
    with open(path, "r") as file:
        lines = [line.strip() for line in file.readlines() if line.strip()]

    player = int(lines[0].split()[0])

    ball = torch.tensor(read_ints(lines[1]), dtype=torch.float32)
    vertices_count = ball.numel()

    allowed_raw = torch.tensor(read_ints(lines[2]), dtype=torch.float32)
    extra_turn = torch.tensor(read_ints(lines[3]), dtype=torch.float32)
    neighbours_raw = torch.tensor(read_ints(lines[4]), dtype=torch.long)


    allowed = allowed_raw.view(vertices_count, 8)
    neighbours = neighbours_raw.view(vertices_count, 8)

    return GameState(
        player=player,
        ball=ball,
        allowed=allowed,
        extra_turn=extra_turn,
        neighbours=neighbours
    )