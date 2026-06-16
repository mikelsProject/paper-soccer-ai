from pathlib import Path
import argparse
import contextlib
import csv
import io
import random
import subprocess
import time

import torch

from parse import load_game_state
from evaluation import best_heuristic_move
from model import PaperSoccerNet
from search_bot import clone_state, apply_move, legal_indices, search_best_move_timed


def project_root():
    return Path(__file__).resolve().parent.parent


def cpp_dir():
    return project_root() / "cpp"


def find_executable():
    candidates = [
        cpp_dir() / "build" / "soccer.exe",
        project_root() / "build" / "soccer.exe",
        cpp_dir() / "build" / "soccer",
        project_root() / "build" / "soccer"
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def reset_initial_state():
    exe = find_executable()

    if exe is None:
        raise FileNotFoundError("Could not find soccer executable. Build the C++ project first.")

    command = [str(exe), "init"]

    subprocess.run(
        command,
        cwd=cpp_dir(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    state_path = cpp_dir() / "gamestate.txt"

    if not state_path.exists():
        raise FileNotFoundError("cpp/gamestate.txt was not created by soccer init.")

    state = load_game_state(state_path)

    if len(legal_indices(state)) == 0:
        raise RuntimeError("Error. Check the C++ init mode.")

    return state


def player_name(player):
    if player == 0:
        return "Top"

    return "Bottom"


class NeuralPlayer:
    def __init__(self, model_path, input_size, device):
        self.device = device
        self.model = PaperSoccerNet(input_size=input_size).to(device)

        if not model_path.exists():
            raise FileNotFoundError(f"saved model not found: {model_path}")

        self.model.load_state_dict(torch.load(model_path, map_location=device))
        self.model.eval()

    def choose_move(self, state):
        state_tensor = state.to_tensor().to(self.device)
        legal_moves = state.legal_moves().to(self.device).bool()

        with torch.no_grad():
            scores = self.model(state_tensor)

        masked_scores = scores.clone()
        masked_scores[:, ~legal_moves] = -1.0e9

        move = int(masked_scores.argmax(dim=1).item())
        score = float(masked_scores[0, move].item())

        return move, score


def choose_move(state, mode, neural_player, search_depth, search_time, silent_search):
    if mode == "heuristic":
        move, score = best_heuristic_move(state)

        return move, score

    if mode == "neural":
        return neural_player.choose_move(state)

    if mode == "search":
        if silent_search:
            with contextlib.redirect_stdout(io.StringIO()):
                move, score = search_best_move_timed(
                    state,
                    max_depth=search_depth,
                    time_limit=search_time
                )
        else:
            move, score = search_best_move_timed(
                state,
                max_depth=search_depth,
                time_limit=search_time
            )

        if move is None:
            move, score = best_heuristic_move(state)

        return move, score

    raise ValueError("Unknown bot mode: " + mode)


def apply_random_opening(state, moves_count, rng):
    opening_moves_done = 0

    for _ in range(moves_count):
        legal = legal_indices(state)

        if len(legal) == 0:
            return True, 1 - state.player, opening_moves_done

        move = rng.choice(legal)
        finished, winner = apply_move(state, move)
        opening_moves_done += 1

        if finished:
            return True, winner, opening_moves_done

    return False, None, opening_moves_done


def play_game(initial_state, top_bot, bottom_bot, neural_player, args, seed):
    rng = random.Random(seed)
    state = clone_state(initial_state)

    finished, winner, opening_moves_done = apply_random_opening(
        state,
        args.opening_random,
        rng
    )

    moves_count = opening_moves_done
    top_time = 0.0
    bottom_time = 0.0
    reason = "normal"

    if finished:
        reason = "opening_finished"

    while not finished and moves_count < args.max_moves:
        current_player = state.player
        current_bot = top_bot if current_player == 0 else bottom_bot

        start = time.time()

        move, score = choose_move(
            state,
            current_bot,
            neural_player,
            args.search_depth,
            args.search_time,
            args.silent_search
        )

        elapsed = time.time() - start

        if current_player == 0:
            top_time += elapsed
        else:
            bottom_time += elapsed

        if move is None:
            finished = True
            winner = 1 - current_player
            reason = "no_move"
            break

        finished, winner = apply_move(state, move)
        moves_count += 1

        if finished:
            reason = "normal"
            break

    if not finished:
        winner = None
        reason = "move_limit"

    winner_side = "Draw"
    winner_bot = "Draw"

    if winner == 0:
        winner_side = "Top"
        winner_bot = top_bot
    elif winner == 1:
        winner_side = "Bottom"
        winner_bot = bottom_bot

    return {
        "top_bot": top_bot,
        "bottom_bot": bottom_bot,
        "winner_side": winner_side,
        "winner_bot": winner_bot,
        "moves": moves_count,
        "reason": reason,
        "final_player": player_name(state.player),
        "final_vertex": state.current_vertex,
        "opening_random": opening_moves_done,
        "top_time": round(top_time, 4),
        "bottom_time": round(bottom_time, 4),
        "seed": seed
    }


def write_results(results, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "game",
        "top_bot",
        "bottom_bot",
        "winner_side",
        "winner_bot",
        "moves",
        "reason",
        "final_player",
        "final_vertex",
        "opening_random",
        "top_time",
        "bottom_time",
        "seed"
    ]

    with open(output_path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for i, row in enumerate(results, start=1):
            row = dict(row)
            row["game"] = i
            writer.writerow(row)


def write_summary(results, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_games = len(results)
    bot_wins = {}
    side_wins = {}
    total_moves = 0

    for row in results:
        bot = row["winner_bot"]
        side = row["winner_side"]

        bot_wins[bot] = bot_wins.get(bot, 0) + 1
        side_wins[side] = side_wins.get(side, 0) + 1
        total_moves += int(row["moves"])

    with open(output_path, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(["metric", "value"])
        writer.writerow(["games", total_games])
        writer.writerow(["average_moves", round(total_moves / max(total_games, 1), 2)])

        for bot, wins in sorted(bot_wins.items()):
            writer.writerow([f"wins_{bot}", wins])

        for side, wins in sorted(side_wins.items()):
            writer.writerow([f"wins_{side}", wins])


def print_summary(results):
    total_games = len(results)
    bot_wins = {}
    side_wins = {}
    total_moves = 0

    for row in results:
        bot_wins[row["winner_bot"]] = bot_wins.get(row["winner_bot"], 0) + 1
        side_wins[row["winner_side"]] = side_wins.get(row["winner_side"], 0) + 1
        total_moves += int(row["moves"])

    print()
    print("Match summary")
    print("----------------")
    print("Games:", total_games)
    print("Average moves:", round(total_moves / max(total_games, 1), 2))

    print()
    print("Wins by bot:")

    for bot, wins in sorted(bot_wins.items()):
        print(bot + ":", wins)

    print()
    print("Wins by side:")

    for side, wins in sorted(side_wins.items()):
        print(side + ":", wins)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--bot-a", default="neural", choices=["neural", "search", "heuristic"])
    parser.add_argument("--bot-b", default="search", choices=["neural", "search", "heuristic"])
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--search-depth", type=int, default=8)
    parser.add_argument("--search-time", type=float, default=0.5)
    parser.add_argument("--opening-random", type=int, default=2)
    parser.add_argument("--max-moves", type=int, default=400)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--silent-search", action="store_true", default=True)

    args = parser.parse_args()

    root = project_root()

    if args.model_path is None:
        model_path = root / "python" / "saved_models" / "policy_model_v3.pth"
    else:
        model_path = Path(args.model_path)

    if args.output is None:
        output_path = root / "python" / "evaluation_results" / "bot_match_results.csv"
    else:
        output_path = Path(args.output)

    summary_path = output_path.parent / "bot_match_summary.csv"

    initial_state = reset_initial_state()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    neural_player = None

    if args.bot_a == "neural" or args.bot_b == "neural":
        neural_player = NeuralPlayer(model_path, initial_state.input_size, device)

    print("Evaluation settings")
    print("-------------------")
    print("Bot A:", args.bot_a)
    print("Bot B:", args.bot_b)
    print("Games:", args.games)
    print("Search depth:", args.search_depth)
    print("Search time:", args.search_time)
    print("Opening random moves:", args.opening_random)
    print("Initial legal moves:", len(legal_indices(initial_state)))
    print("Initial vertex:", initial_state.current_vertex)
    print("Device:", device)
    print("Output:", output_path)

    if args.games > 1 and args.opening_random == 0:
        print()
        print("Warning: no random opening moves, all games might be the same")

    results = []

    for game_id in range(args.games):
        if game_id % 2 == 0:
            top_bot = args.bot_a
            bottom_bot = args.bot_b
        else:
            top_bot = args.bot_b
            bottom_bot = args.bot_a

        seed = args.seed + game_id

        row = play_game(
            initial_state,
            top_bot,
            bottom_bot,
            neural_player,
            args,
            seed
        )

        results.append(row)

        print(
            "Game",
            game_id + 1,
            "| Top:",
            top_bot,
            "| Bottom:",
            bottom_bot,
            "| Winner:",
            row["winner_bot"],
            "| Moves:",
            row["moves"],
            "| Reason:",
            row["reason"]
        )

    write_results(results, output_path)
    write_summary(results, summary_path)
    print_summary(results)

    print()
    print("Saved results to:", output_path)
    print("Saved summary to:", summary_path)


if __name__ == "__main__":
    main()
