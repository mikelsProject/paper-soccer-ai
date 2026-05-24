import torch
from torch.utils.data import Dataset


class PaperSoccerDataset(Dataset):
    def __init__(self, states, moves):
        self.states = states.float()
        self.moves = moves.long()

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        return self.states[idx], self.moves[idx]
