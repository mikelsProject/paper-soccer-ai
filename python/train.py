from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset, random_split

from model import PaperSoccerNet


def mask_outputs(outputs, legal_masks): # masks illegal moves so the model cannot select them
    masked_outputs = outputs.clone()
    masked_outputs[~legal_masks] = -1.0e4 # safe value for mixed precision, illegal moves get very low score

    return masked_outputs


def soft_target_loss(outputs, targets, legal_masks): # trains the model to match the expert score distribution
    masked_outputs = mask_outputs(outputs, legal_masks)

    masked_targets = targets.clone()
    masked_targets[~legal_masks] = -1.0e4 # illegal target moves should have almost zero probability

    temperature = 0.5 # smaller values makes the best moves more important, but still keeps close alternatives

    target_probs = torch.softmax(masked_targets / temperature, dim=1) # converting expert scores into probabilities
    log_probs = F.log_softmax(masked_outputs, dim=1) # converting model outputs into log probabilities

    loss = -(target_probs * log_probs).sum(dim=1).mean() # soft cross entropy

    return loss


def masked_cross_entropy_loss(outputs, best_moves, legal_masks): # classification loss for exact best move
    masked_outputs = mask_outputs(outputs, legal_masks)

    loss = F.cross_entropy(masked_outputs, best_moves) # compares predicted move scores with the expert best move

    return loss


def combined_loss(outputs, targets, legal_masks, best_moves): # combines soft score learning and exact best move learning
    soft = soft_target_loss(outputs, targets, legal_masks) # learns from all expert scores, not only one move
    hard = masked_cross_entropy_loss(outputs, best_moves, legal_masks) # still keeps some pressure on the exact best move

    loss = 0.70 * soft + 0.30 * hard

    return loss


def exact_accuracy(outputs, best_moves, legal_masks): # function calculates the exact accuracy by masking the outputs to only consider legal moves and then checking if the best move is with the highest predicted value
    masked_outputs = mask_outputs(outputs, legal_masks)

    preds = masked_outputs.argmax(dim=1) # we get the indices of the highest predicted values for each sample, which correspond to the predicted best moves
    correct = (preds == best_moves).sum().item() # compare the predicted best moves with the actual best moves and count how many are correct

    return correct


def top3_accuracy(outputs, best_moves, legal_masks): # function calculates the top3 accuracy by masking the outputs to only consider legal moves and then checking if the best move is among the top 3 predicted moves
    masked_outputs = mask_outputs(outputs, legal_masks)

    _, top3 = masked_outputs.topk(3, dim=1) # we get the indices of the top 3 predicted values for each sample, which correspond to the top 3 predicted moves
    correct = top3.eq(best_moves.view(-1, 1)).sum().item()

    return correct


def train_one_epoch(model, loader, optimizer, scaler, device, use_amp): # function trains the model for one epoch and calculates the average loss, accuracy, and top3 accuracy on the training set
    model.train()

    total_loss = 0.0
    correct = 0
    top3_correct = 0
    total = 0

    for states, targets, legal_masks, best_moves in loader: # we iterate over the training data in batches, moving the data to the specified device and then we calculate the outputs of the model, the loss and update the model parameters using backpropagation.
        states = states.to(device, non_blocking=True)
        targets = targets.to(device, non_blocking=True)
        legal_masks = legal_masks.to(device, non_blocking=True)
        best_moves = best_moves.to(device, non_blocking=True)

        optimizer.zero_grad()

        if use_amp:
            with torch.autocast(device_type="cuda", dtype=torch.float16):
                outputs = model(states)
                loss = combined_loss(outputs, targets, legal_masks, best_moves)

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0) # prevents very large gradients

            scaler.step(optimizer)
            scaler.update()
        else:
            outputs = model(states)
            loss = combined_loss(outputs, targets, legal_masks, best_moves)

            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0) # prevents very large gradients

            optimizer.step()

        total_loss += loss.item()
        correct += exact_accuracy(outputs.detach(), best_moves, legal_masks)
        top3_correct += top3_accuracy(outputs.detach(), best_moves, legal_masks)
        total += states.size(0)

    avg_loss = total_loss / len(loader)
    acc = correct / total
    top3 = top3_correct / total

    return avg_loss, acc, top3


def evaluate(model, loader, device, use_amp): # function evaluates the model on the test set and calculates the average loss, accuracy, and top3 accuracy
    model.eval()

    total_loss = 0.0
    correct = 0
    top3_correct = 0
    total = 0

    with torch.no_grad(): # we disable gradient calculation since we are only evaluating
        for states, targets, legal_masks, best_moves in loader:
            states = states.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)
            legal_masks = legal_masks.to(device, non_blocking=True)
            best_moves = best_moves.to(device, non_blocking=True)

            if use_amp:
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    outputs = model(states)
                    loss = combined_loss(outputs, targets, legal_masks, best_moves)
            else:
                outputs = model(states)
                loss = combined_loss(outputs, targets, legal_masks, best_moves)

            total_loss += loss.item()
            correct += exact_accuracy(outputs, best_moves, legal_masks)
            top3_correct += top3_accuracy(outputs, best_moves, legal_masks)
            total += states.size(0)

    avg_loss = total_loss / len(loader)
    acc = correct / total
    top3 = top3_correct / total

    return avg_loss, acc, top3


def main():
    torch.manual_seed(42)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(42)
        torch.set_float32_matmul_precision("high")

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
    use_amp = device.type == "cuda"

    print("Device:", device)
    print("Training mode: soft targets + small hard CE, no MSE")

    states = torch.load(states_path).float() # putting data into tensors and converting to float
    targets = torch.load(targets_path).float()
    legal_masks = torch.load(legal_masks_path).bool()
    best_moves = torch.load(best_moves_path).long()

    print("Dataset size:", states.shape[0])
    print("Input size:", states.shape[1])
    print("Targets shape:", targets.shape)
    print("Legal masks shape:", legal_masks.shape)

    print("Targets min:", round(float(targets.min().item()), 4))
    print("Targets max:", round(float(targets.max().item()), 4))
    print("Targets mean:", round(float(targets.mean().item()), 4))

    illegal_best = legal_masks.gather(1, best_moves.view(-1, 1)).squeeze(1) == False

    if illegal_best.any():
        print("Warning: some best moves are marked as illegal.")
        print("Invalid samples:", int(illegal_best.sum().item()))

        keep = ~illegal_best
        states = states[keep]
        targets = targets[keep]
        legal_masks = legal_masks[keep]
        best_moves = best_moves[keep]

        print("Dataset size after removing invalid samples:", states.shape[0])

    print("Best move distribution:") # checking the distribution of best moves in the dataset to see if there is any imbalance that could make training difficult
    counts = torch.bincount(best_moves, minlength=8)

    for i, count in enumerate(counts):
        print(i, count.item())

    dataset = TensorDataset(states, targets, legal_masks, best_moves) # creating a dataset from the tensors

    train_size = int(0.9 * len(dataset)) # splitting the dataset into training and test sets (90% - training, 10% - testing)
    test_size = len(dataset) - train_size

    train_dataset, test_dataset = random_split( # randomly splitting the samples
        dataset,
        [train_size, test_size],
        generator=torch.Generator().manual_seed(42)
    )

    num_workers = 2 if device.type == "cuda" else 0
    pin_memory = device.type == "cuda"

    train_loader = DataLoader(
        train_dataset,
        batch_size=512,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=num_workers > 0
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=512,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        persistent_workers=num_workers > 0
    )

    model = PaperSoccerNet(input_size=states.shape[1]).to(device)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=0.0002,
        weight_decay=1.0e-4
    )

    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=35,
        min_lr=1.0e-6
    )

    scaler = torch.amp.GradScaler("cuda", enabled=use_amp)

    epochs = 500

    best_test_acc = 0.0
    best_test_top3 = 0.0
    best_test_loss = 1.0e9

    best_model_path = model_dir / "policy_model_v3.pth"
    final_model_path = model_dir / "policy_model_v3_final.pth"
    history = []

    for epoch in range(epochs):
        train_loss, train_acc, train_top3 = train_one_epoch(
            model,
            train_loader,
            optimizer,
            scaler,
            device,
            use_amp
        )

        test_loss, test_acc, test_top3 = evaluate( # this one trains the model for one epoch and then evaluates it on the test set to see how well it is doing and then it saves the best model based on the exact accuracy on the test set
            model,
            test_loader,
            device,
            use_amp
        )

        scheduler.step(test_acc)

        should_save = False

        if test_acc > best_test_acc: # exact accuracy is the most important metric because the neural bot chooses only one move
            should_save = True
        elif test_acc == best_test_acc and test_top3 > best_test_top3:
            should_save = True
        elif test_acc == best_test_acc and test_top3 == best_test_top3 and test_loss < best_test_loss:
            should_save = True

        if should_save:
            best_test_acc = test_acc
            best_test_top3 = test_top3
            best_test_loss = test_loss
            torch.save(model.state_dict(), best_model_path)

        current_lr = optimizer.param_groups[0]["lr"]

        print(
            f"Epoch {epoch + 1}/{epochs}, "
            f"LR: {current_lr:.6f}, "
            f"Train loss: {train_loss:.4f}, "
            f"Train accuracy: {train_acc:.4f}, "
            f"Train top3: {train_top3:.4f}, "
            f"Test loss: {test_loss:.4f}, "
            f"Test accuracy: {test_acc:.4f}, "
            f"Test top3: {test_top3:.4f}, "
            f"Best test accuracy: {best_test_acc:.4f}"
        )

        history.append([
            epoch + 1,
            current_lr,
            train_loss,
            train_acc,
            train_top3,
            test_loss,
            test_acc,
            test_top3,
            best_test_acc
        ])

    torch.save(model.state_dict(), final_model_path)

    history_path = model_dir / "training_history_v3.csv" # saving the training history so I can plot it
    with open(history_path, "w") as file:
        file.write("epoch,lr,train_loss,train_acc,train_top3,test_loss,test_acc,test_top3,best_test_acc\n")

        for row in history:
            file.write(",".join(str(x) for x in row) + "\n")

    print("Saved training history to:", history_path)

    print()
    print("Saved best model to:", best_model_path)
    print("Saved final model to:", final_model_path)
    print("Best test accuracy:", round(best_test_acc, 4))
    print("Best test top3 accuracy:", round(best_test_top3, 4))


if __name__ == "__main__":
    main()