import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from model import PaperSoccerNet
from dataset import PaperSoccerDataset


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

input_size = 256

states = torch.randint(0, 2, (1000, input_size)).float()
moves = torch.randint(0, 8, (1000,))

dataset = PaperSoccerDataset(states, moves)
train_loader = DataLoader(dataset, batch_size=64, shuffle=True)

model = PaperSoccerNet(input_size).to(device)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

epochs = 10

for epoch in range(epochs):
    model.train()

    total_loss = 0
    correct = 0
    total = 0

    for batch_states, batch_moves in train_loader:
        batch_states = batch_states.to(device)
        batch_moves = batch_moves.to(device)

        outputs = model(batch_states)
        loss = criterion(outputs, batch_moves)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

        preds = outputs.argmax(dim=1)
        correct += (preds == batch_moves).sum().item()
        total += batch_moves.size(0)

    accuracy = correct / total

    print(f"Epoch {epoch + 1}/{epochs}, Loss: {total_loss:.4f}, Accuracy: {accuracy:.4f}")

torch.save(model.state_dict(), "python/saved_models/policy_model.pth")