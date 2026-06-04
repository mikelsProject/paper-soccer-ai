import torch
import torch.nn as nn


class PaperSoccerNet(nn.Module):
    def __init__(self, input_size):
        super().__init__()

        self.model = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.ReLU(),

            nn.Linear(512, 256),
            nn.ReLU(),

            nn.Linear(256, 128),
            nn.ReLU(),

            nn.Linear(128, 8)
        )

    def forward(self, x):
        return self.model(x)


def choose_move(model, state_tensor, legal_moves):
    model.eval()

    with torch.no_grad():
        scores = model(state_tensor)

    legal_moves = legal_moves.to(dtype=torch.bool, device=scores.device) # we convert legal_moves to boolean mask and move it to the same device as scores

    masked_scores = scores.clone() # we create a copy of scores to avoid modifying the original scores tensor - we will set the scores of illegal moves to -inf so they won't be chosen as the best move
    masked_scores[:, ~legal_moves] = float("-inf")

    return masked_scores.argmax(dim=1).item()
