from pathlib import Path
import csv

import matplotlib.pyplot as plt


def project_root():
    return Path(__file__).resolve().parent.parent


def read_csv(path):
    with open(path, "r", newline="") as file:
        return list(csv.DictReader(file))


def to_float(rows, key):
    return [float(row[key]) for row in rows]


def save_training_accuracy(history_path, output_dir):
    rows = read_csv(history_path)

    epochs = to_float(rows, "epoch")
    train_acc = to_float(rows, "train_acc")
    test_acc = to_float(rows, "test_acc")
    train_top3 = to_float(rows, "train_top3")
    test_top3 = to_float(rows, "test_top3")

    plt.figure(figsize=(9, 5))
    plt.plot(epochs, train_acc, label="Train accuracy")
    plt.plot(epochs, test_acc, label="Test accuracy")
    plt.plot(epochs, train_top3, label="Train top-3")
    plt.plot(epochs, test_top3, label="Test top-3")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.title("Paper Soccer neural bot training accuracy")
    plt.legend()
    plt.tight_layout()

    path = output_dir / "training_accuracy.png"
    plt.savefig(path, dpi=160)
    plt.close()

    return path


def save_training_loss(history_path, output_dir):
    rows = read_csv(history_path)

    epochs = to_float(rows, "epoch")
    train_loss = to_float(rows, "train_loss")
    test_loss = to_float(rows, "test_loss")

    plt.figure(figsize=(9, 5))
    plt.plot(epochs, train_loss, label="Train loss")
    plt.plot(epochs, test_loss, label="Test loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.title("Paper Soccer neural bot training loss")
    plt.legend()
    plt.tight_layout()

    path = output_dir / "training_loss.png"
    plt.savefig(path, dpi=160)
    plt.close()

    return path


def save_learning_rate(history_path, output_dir):
    rows = read_csv(history_path)

    if len(rows) == 0 or "lr" not in rows[0]:
        return None

    epochs = to_float(rows, "epoch")
    lr = to_float(rows, "lr")

    plt.figure(figsize=(9, 5))
    plt.plot(epochs, lr, label="Learning rate")
    plt.xlabel("Epoch")
    plt.ylabel("Learning rate")
    plt.title("Learning rate during training")
    plt.legend()
    plt.tight_layout()

    path = output_dir / "learning_rate.png"
    plt.savefig(path, dpi=160)
    plt.close()

    return path


def save_bot_wins(results_path, output_dir):
    if not results_path.exists():
        return None

    rows = read_csv(results_path)
    wins = {}

    for row in rows:
        bot = row["winner_bot"]
        wins[bot] = wins.get(bot, 0) + 1

    names = list(wins.keys())
    values = [wins[name] for name in names]

    plt.figure(figsize=(7, 5))
    plt.bar(names, values)
    plt.xlabel("Bot")
    plt.ylabel("Wins")
    plt.title("Bot match results")
    plt.tight_layout()

    path = output_dir / "bot_match_wins.png"
    plt.savefig(path, dpi=160)
    plt.close()

    return path


def save_game_lengths(results_path, output_dir):
    if not results_path.exists():
        return None

    rows = read_csv(results_path)

    games = [int(row["game"]) for row in rows]
    moves = [int(row["moves"]) for row in rows]

    plt.figure(figsize=(9, 5))
    plt.plot(games, moves, marker="o", label="Moves")
    plt.xlabel("Game")
    plt.ylabel("Moves")
    plt.title("Length of bot evaluation games")
    plt.legend()
    plt.tight_layout()

    path = output_dir / "bot_match_lengths.png"
    plt.savefig(path, dpi=160)
    plt.close()

    return path


def main():
    root = project_root()

    history_path = root / "python" / "saved_models" / "training_history_v2.csv"
    results_path = root / "python" / "evaluation_results" / "bot_match_results.csv"
    output_dir = root / "python" / "plots"

    output_dir.mkdir(exist_ok=True)

    if not history_path.exists():
        print("No training history found:", history_path)
    else:
        path = save_training_accuracy(history_path, output_dir)
        print("Saved:", path)

        path = save_training_loss(history_path, output_dir)
        print("Saved:", path)

        path = save_learning_rate(history_path, output_dir)

        if path is not None:
            print("Saved:", path)

    if results_path.exists():
        path = save_bot_wins(results_path, output_dir)

        if path is not None:
            print("Saved:", path)

        path = save_game_lengths(results_path, output_dir)

        if path is not None:
            print("Saved:", path)
    else:
        print("No bot evaluation results found yet:", results_path)


if __name__ == "__main__":
    main()
