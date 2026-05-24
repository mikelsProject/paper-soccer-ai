import torch
from model import PaperSoccerNet


input_size = 256

model = PaperSoccerNet(input_size)

dummy_state = torch.zeros(1, input_size)

output = model(dummy_state)

print("Output:", output)
print("Output shape:", output.shape)