import torch
import torch.nn as nn


class PaperSoccerNet(nn.Module):
    def __init__(self, input_size, hidden_size=128):
        super().__init__()

        self.model = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),

            nn.Linear(hidden_size, 64),
            nn.ReLU(),

            nn.Linear(64, 8)
        )

    def forward(self, x):
        return self.model(x)


