from pathlib import Path
import random
import torch

from parse import load_game_state
from search_bot import (
    clone_state,
    apply_move,
    legal_indices,
    negamax,
    terminal_value
)


def move_scores(state, depth):
    scores = torch.full((8,), -1000.0)
    legal_mask = torch.zeros(8, dtype=torch.bool)

    moves = legal_indices(state)

    if len(moves) == 0:
        return scores, legal_mask, None

    table = {}

    for move in moves:
        legal_mask[move] = True # only legal moves

        child = clone_state(state)
        finished, winner = apply_move(child, move)

        if finished:
            value = terminal_value(winner, state.player)
        else:
            if child.player == state.player: # if the player gets an extra turn, we don't negate the value because it's still the same player's turn, otherwise we negate the value because its the turn of the opponent
                value = negamax(child, depth - 1, -1.0e9, 1.0e9, table)
            else:
                value = -negamax(child, depth - 1, -1.0e9, 1.0e9, table)

        scores[move] = float(value)

    best_move = int(torch.argmax(scores).item()) # returnign best score

    return scores, legal_mask, best_move


def normalize_scores(scores, legal_mask): # normalizing the scores of the legal moves
    targets = torch.zeros(8)

    legal_scores = scores[legal_mask] # only legal moves are considered for normalization

    if legal_scores.numel() == 0:
        return targets

    legal_scores = torch.clamp(legal_scores, -20.0, 20.0) # avoiding extreme values that could make training really unstable

    mean = legal_scores.mean() # normalizing to have mean 0 and std 1, which helps with training

    if legal_scores.numel() == 1: # if there is only one legal move, we can't normalize it, so we just set it to 0 (the mean)
        targets[legal_mask] = 0.0

        return targets

    std = legal_scores.std(unbiased=False) # if the standard deviation is very small, we avoid division by zero and just subtract the mean without dividing by std, which means all legal moves will have the same score (0) and the model won't learn to prefer one over the others in this case, but that's better than having NaN in the targets which would make training impossible

    if std.item() < 1.0e-6: # 
        normalized = legal_scores - mean
    else:
        normalized = (legal_scores - mean) / std

    targets[legal_mask] = normalized # only legal moves get the normalized scores, illegal moves stay at 0 which means they are not preferred

    return targets


def choose_simulation_move(scores, legal_mask, epsilon):
    legal_moves = [i for i in range(8) if legal_mask[i]] # getting the indices of the legal moves

    if len(legal_moves) == 0:
        return None

    if random.random() < epsilon: # with probability epsilon we are choosing random legal move
        return random.choice(legal_moves)

    return int(torch.argmax(scores).item())


def main():
    project_root = Path(__file__).resolve().parent.parent

    state_path = project_root / "cpp" / "gamestate.txt"
    data_dir = project_root / "python" / "data"

    data_dir.mkdir(exist_ok=True)

    states_path = data_dir / "states.pt"
    targets_path = data_dir / "targets.pt"
    legal_masks_path = data_dir / "legal_masks.pt"
    best_moves_path = data_dir / "best_moves.pt"

    initial_state = load_game_state(state_path)

    initial_legal = legal_indices(initial_state)

    print("Initial player:", initial_state.player)
    print("Initial vertex:", initial_state.current_vertex)
    print("Initial legal moves:", initial_legal)

    if len(initial_legal) == 0:
        print()
        print("No legal moves in gamestate.txt")

        return

    games_count = 10000
    max_moves_per_game = 400
    epsilon = 0.30
    expert_depth = 5

    states = []
    targets = []
    legal_masks = []
    best_moves = []

    seen_states = set()

    for game_id in range(games_count): # simulating games to generate training data, we use the expert bot to choose the moves and we add some randomness to get more diverse samples
        state = clone_state(initial_state)

        for step in range(max_moves_per_game): # we are limitting the number of moves per game
            legal = legal_indices(state)

            if len(legal) == 0:
                break

            key = ( # we create a unique key for the state based on the player, current vertex and legal moves, so we can check if we have already seen this state before and avoid adding duplicate samples to the dataset
                state.player,
                state.current_vertex,
                tuple(state.allowed.flatten().int().tolist()),
                tuple(state.extra_turn.int().tolist())
            )

            scores, legal_mask, best_move = move_scores(state, expert_depth)

            if best_move is None: # no best move
                break

            if key not in seen_states: # we only add the state to the dataset if we haven't seen it before
                seen_states.add(key)

                state_tensor = state.to_tensor().squeeze(0)
                target_scores = normalize_scores(scores, legal_mask)

                states.append(state_tensor)
                targets.append(target_scores)
                legal_masks.append(legal_mask)
                best_moves.append(best_move)

            simulation_move = choose_simulation_move(scores, legal_mask, epsilon)

            if simulation_move is None:
                break

            finished, winner = apply_move(state, simulation_move)

            if finished:
                break

        if (game_id + 1) % 10 == 0: # printing after every 10 games
            print(
                "Generated games:",
                game_id + 1,
                "unique samples:",
                len(states)
            )

    if len(states) == 0:
        print()
        print("No samples generated.")
        return

    states = torch.stack(states)
    targets = torch.stack(targets)
    legal_masks = torch.stack(legal_masks)
    best_moves = torch.tensor(best_moves, dtype=torch.long)

    torch.save(states, states_path)
    torch.save(targets, targets_path)
    torch.save(legal_masks, legal_masks_path)
    torch.save(best_moves, best_moves_path)

    print()
    print("Dataset v2 generated")
    print("States shape:", states.shape)
    print("Targets shape:", targets.shape)
    print("Legal masks shape:", legal_masks.shape)
    print("Best moves shape:", best_moves.shape)

    print()
    print("Saved:", states_path)
    print("Saved:", targets_path)
    print("Saved:", legal_masks_path)
    print("Saved:", best_moves_path)


if __name__ == "__main__":
    main()