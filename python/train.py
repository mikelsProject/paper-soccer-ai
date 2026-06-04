from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset, random_split

from model import PaperSoccerNet


def masked_mse_loss(outputs, targets, legal_masks): # calculates the mean squared error loss
    mask = legal_masks.float() # we only want to calculate the loss for the legal moves

    diff = (outputs - targets) * mask # we calculate the difference between the outputs and targets and then we multiply it by the mask to only keep the legal moves
    loss = (diff * diff).sum() / mask.sum()

    return loss


def exact_accuracy(outputs, best_moves, legal_masks): # function calculates the exact accuracy by masking the outputs to only consider legal moves and then checking if the best move is with the highest predicted value
    masked_outputs = outputs.clone() # we create a copy of the outputs so we don't modify the original tensor
    masked_outputs[~legal_masks] = -1.0e9 # we set the values of the illegal moves to a very large negative number so they won't be selected as the best move

    preds = masked_outputs.argmax(dim=1) # we get the indices of the highest predicted values for each sample, which correspond to the predicted best moves
    correct = (preds == best_moves).sum().item() # compare the predicted best moves with the actual best moves and count how many are correct

    return correct


def top3_accuracy(outputs, best_moves, legal_masks): # function calculates the top3 accuracy by masking the outputs to only consider legal moves and then checking if the best move is among the top 3 predicted moves
    masked_outputs = outputs.clone()
    masked_outputs[~legal_masks] = -1.0e9

    _, top3 = masked_outputs.topk(3, dim=1) # we get the indices of the top 3 predicted values for each sample, which correspond to the top 3 predicted moves
    correct = top3.eq(best_moves.view(-1, 1)).sum().item()

    return correct


def train_one_epoch(model, loader, optimizer, device): # function trains the model for one epoch and calculates the average loss, accuracy, and top3 accuracy on the training set
    model.train()

    total_loss = 0.0
    correct = 0
    top3_correct = 0
    total = 0

    for states, targets, legal_masks, best_moves in loader: # we iterate over the training data in batches, moving the data to the specified device and then we calculate the outputs of the model, the loss and update the model parameters using backpropagation.
        states = states.to(device)
        targets = targets.to(device)
        legal_masks = legal_masks.to(device)
        best_moves = best_moves.to(device)

        outputs = model(states)
        loss = masked_mse_loss(outputs, targets, legal_masks)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()
        correct += exact_accuracy(outputs, best_moves, legal_masks)
        top3_correct += top3_accuracy(outputs, best_moves, legal_masks)
        total += states.size(0)

    avg_loss = total_loss / len(loader)
    acc = correct / total
    top3 = top3_correct / total

    return avg_loss, acc, top3


def evaluate(model, loader, device): # function evaluates the model on the test set and calculates the average loss, accuracy, and top3 accuracy
    model.eval()

    total_loss = 0.0
    correct = 0
    top3_correct = 0
    total = 0

    with torch.no_grad(): # we disable gradient calculation since we are only evaluating
        for states, targets, legal_masks, best_moves in loader:
            states = states.to(device)
            targets = targets.to(device)
            legal_masks = legal_masks.to(device)
            best_moves = best_moves.to(device)

            outputs = model(states)
            loss = masked_mse_loss(outputs, targets, legal_masks)

            total_loss += loss.item()
            correct += exact_accuracy(outputs, best_moves, legal_masks)
            top3_correct += top3_accuracy(outputs, best_moves, legal_masks)
            total += states.size(0)

    avg_loss = total_loss / len(loader)
    acc = correct / total
    top3 = top3_correct / total

    return avg_loss, acc, top3


def main():
    project_root = Path(__file__).resolve().parent.parent

    data_dir = project_root / "python" / "data"
    model_dir = project_root / "python" / "saved_models"

    states_path = data_dir / "states.pt"
    targets_path = data_dir / "targets.pt"
    legal_masks_path = data_dir / "legal_masks.pt"
    best_moves_path = data_dir / "best_moves.pt"

    model_dir.mkdir(exist_ok=True)


    required_files = [
    states_path,
    targets_path,
    legal_masks_path,
    best_moves_path
    ]

    missing_files = [path.name for path in required_files if not path.exists()]

    if len(missing_files) > 0:
        print("Missing files:", ", ".join(missing_files))
        print("Run generate_dataset.py to generate the dataset before doing the training") # users have to generate the dataset before doing training

        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("Device:", device)

    states = torch.load(states_path).float() # putting data into tensors and converting to float
    targets = torch.load(targets_path).float()
    legal_masks = torch.load(legal_masks_path).bool()
    best_moves = torch.load(best_moves_path).long()

    print("Dataset size:", states.shape[0])
    print("Input size:", states.shape[1])
    print("Targets shape:", targets.shape)
    print("Legal masks shape:", legal_masks.shape)

    print("Best move distribution:") # checking the distribution of best moves in the dataset to see if there is any imbalance that could make training difficult
    counts = torch.bincount(best_moves, minlength=8)

    for i, count in enumerate(counts):
        print(i, count.item())

    dataset = TensorDataset(states, targets, legal_masks, best_moves) # creating a dataset from the tensors

    train_size = int(0.8 * len(dataset)) # splitting the dataset into training and test sets (80% - training, 20% - testing)
    test_size = len(dataset) - train_size

    train_dataset, test_dataset = random_split( # randomly splitting the samples
        dataset,
        [train_size, test_size],
        generator=torch.Generator().manual_seed(42)
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=128,
        shuffle=True
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=128,
        shuffle=False
    )

    model = PaperSoccerNet(input_size=states.shape[1]).to(device)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=0.0005,
        weight_decay=1.0e-5
    )

    epochs = 80

    best_test_top3 = 0.0
    best_model_path = model_dir / "policy_model_v2.pth"
    history = []

    for epoch in range(epochs):
        train_loss, train_acc, train_top3 = train_one_epoch(
            model,
            train_loader,
            optimizer,
            device
        )

        test_loss, test_acc, test_top3 = evaluate( # this one trains the model for one epoch and then evaluates it on the test set to see how well it is doing and then it saves the best model based on the top3 accuracy on the test set
            model,
            test_loader,
            device
        )

        if test_top3 > best_test_top3:
            best_test_top3 = test_top3
            torch.save(model.state_dict(), best_model_path)

        print(
            f"Epoch {epoch + 1}/{epochs}, "
            f"Train loss: {train_loss:.4f}, "
            f"Train accuracy: {train_acc:.4f}, "
            f"Train top3: {train_top3:.4f}, "
            f"Test loss: {test_loss:.4f}, "
            f"Test accuracy: {test_acc:.4f}, "
            f"Test top3: {test_top3:.4f}"
        )

        history.append([
            epoch + 1,
            train_loss,
            train_acc,
            train_top3,
            test_loss,
            test_acc,
            test_top3
        ])

    history_path = model_dir / "training_history_v2.csv" # saving the training history so we can plot it
    with open(history_path, "w") as file:
        file.write("epoch,train_loss,train_acc,train_top3,test_loss,test_acc,test_top3\n")

        for row in history:
            file.write(",".join(str(x) for x in row) + "\n")

    print("Saved training history to:", history_path)

    print()
    print("Saved best model to:", best_model_path)
    print("Best test top3 accuracy:", round(best_test_top3, 4))


if __name__ == "__main__":
    main()