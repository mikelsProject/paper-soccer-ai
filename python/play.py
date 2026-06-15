import sys
from pathlib import Path

import torch

from parse import load_game_state
from evaluation import best_heuristic_move, print_move_scores, direction_names
from model import PaperSoccerNet, choose_move
from search_bot import search_best_move_timed


def project_root():
    return Path(__file__).resolve().parent.parent


def find_state_file():
    path = project_root() / "cpp" / "gamestate.txt"

    if not path.exists():
        raise FileNotFoundError(f"no gamestate.txt file at: {path}")

    return path


def get_move_output_file():
    return project_root() / "cpp" / "move.txt" # using move.txt


def save_move(move):
    path = get_move_output_file()

    with open(path, "w") as file:
        file.write(str(move))

    return path


def choose_heuristic(state):
    move, score = best_heuristic_move(state)

    return move, score


def choose_search(state, max_depth=8, time_limit=2.0): # depth is maximum = 8 for every layer maximum time is 2s
    move, score = search_best_move_timed(
        state,
        max_depth=max_depth,
        time_limit=time_limit
    )

    return move, score


def choose_neural(state):
    model_path = project_root() / "python" / "saved_models" / "policy_model_v2.pth"

    model = PaperSoccerNet(input_size=state.input_size)

    if model_path.exists():
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        print("Loaded model:", model_path)
    else:
        print("Saved model not found.")
        return None, 0.0

    model.eval()

    state_tensor = state.to_tensor()
    legal_moves = state.legal_moves()

    with torch.no_grad():
        scores = model(state_tensor)

    legal_moves = legal_moves.bool() # making sure legal_moves is a boolean tensor so we can use it for masking

    masked_scores = scores.clone()
    masked_scores[:, ~legal_moves] = -1.0e9

    move = int(masked_scores.argmax(dim=1).item())
    score = float(masked_scores[0, move].item())

    print()
    print("Neural predicted scores:")

    for i in range(8):
        if legal_moves[i]:
            print(i, direction_names[i], "score:", round(float(scores[0, i].item()), 4))

    return move, score


def main():
    mode = "search"
    max_depth = 8
    time_limit = 1.7

    if len(sys.argv) > 1:
        mode = sys.argv[1]

    if len(sys.argv) > 2:
        max_depth = int(sys.argv[2])

    if len(sys.argv) > 3:
        time_limit = float(sys.argv[3])

    state_path = find_state_file()

    print("Using state file:", state_path)
    print("Mode:", mode)

    state = load_game_state(state_path)

    print()
    print("Player:", state.player)
    print("Vertices:", state.vertices_count)
    print("Current vertex:", state.current_vertex)
    print("Input size:", state.input_size)

    legal_moves = state.legal_moves()
    legal_count = int(legal_moves.sum().item())

    print()
    print("Legal moves count:", legal_count)

    if legal_count == 0:
        print("No legal moves available.")
        return

    print()
    print("Legal moves and heuristic scores:")
    print_move_scores(state)

    print()

    if mode == "heuristic":
        move, score = choose_heuristic(state)
    elif mode == "search":
        move, score = choose_search(state, max_depth, time_limit)
    elif mode == "neural":
        move, score = choose_neural(state)
    else:
        raise ValueError("Unknown mode, use: heuristic, search, neural")

    if move is None:
        print("no move was selected")
        return

    print()
    print("Selected move:", move, direction_names[move])
    print("Score:", round(score, 4))

    move_path = save_move(move)

    print()
    print("Saved move to:", move_path)


if __name__ == "__main__":
    main()