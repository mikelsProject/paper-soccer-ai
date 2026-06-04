import torch
from torch.utils.data import Dataset


class PaperSoccerDataset(Dataset): # creating the dataset
    def __init__(self, states_path, moves_path):
        self.states = torch.load(states_path).float()
        self.moves = torch.load(moves_path).long()

    def __len__(self):
        return len(self.states)

    def __getitem__(self, idx):
        return self.states[idx], self.moves[idx]