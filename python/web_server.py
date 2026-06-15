from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import contextlib
import csv
import io
import json
import random
import subprocess
import threading
import time

import torch

from parse import load_game_state
from evaluation import best_heuristic_move, direction_names
from model import PaperSoccerNet
from search_bot import clone_state, apply_move, legal_indices, search_best_move_timed


width = 11
height = 13
goal_width = 5

game_process = None
active_mode = "human"
state_lock = threading.Lock()

current_settings = {
    "side": 1,
    "mode": "search",
    "depth": 8,
    "time": 2.0
}

live_state = None
live_running = False
live_finished = False
live_winner = None
live_moves = 0
live_last_step = 0.0
live_last_move = None
live_last_bot = None
live_last_score = 0.0
live_last_target = None
live_top_time = 0.0
live_bottom_time = 0.0
live_result_saved = False
live_neural_player = None
live_random_opening = 3
live_rng = random.Random()

live_settings = {
    "top_bot": "neural",
    "bottom_bot": "search",
    "depth": 8,
    "time": 0.5,
    "delay": 0.3,
    "max_moves": 400,
    "random_opening": 3
}


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


def project_root():
    return Path(__file__).resolve().parent.parent


def cpp_dir():
    return project_root() / "cpp"


def cpp_path(name):
    return cpp_dir() / name


def python_dir():
    return project_root() / "python"


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


def clean_game_files():
    names = [
        "web_move.txt",
        "move.txt",
        "web_status.txt",
        "bot_log.txt",
        "game_log.txt"
    ]

    for name in names:
        path = cpp_path(name)

        if path.exists():
            path.unlink()


def stop_game():
    global game_process

    if game_process is not None and game_process.poll() is None:
        game_process.terminate()

        try:
            game_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            game_process.kill()

    game_process = None


def reset_initial_state():
    exe = find_executable()

    if exe is None:
        raise FileNotFoundError("Could not find soccer.exe. Build the C++ project first.")

    subprocess.run(
        [str(exe), "init"],
        cwd=cpp_dir(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    state_path = cpp_path("gamestate.txt")

    if not state_path.exists():
        raise FileNotFoundError("cpp/gamestate.txt was not created by soccer init.")

    state = load_game_state(state_path)

    if len(legal_indices(state)) == 0:
        raise RuntimeError("Fresh initial state has no legal moves. Check the C++ init mode.")

    return state


def start_game(settings):
    global game_process, current_settings, active_mode
    global live_running, live_finished

    stop_game()
    clean_game_files()

    live_running = False
    live_finished = False
    active_mode = "human"

    exe = find_executable()

    if exe is None:
        cpp_path("web_status.txt").write_text("executable_not_found")

        return False, "Could not find soccer.exe. Build the C++ project first."

    side = int(settings.get("side", 1))
    mode = str(settings.get("mode", "search"))

    if mode not in ["heuristic", "search", "neural"]:
        mode = "search"

    depth = int(settings.get("depth", 8))
    thinking_time = float(settings.get("time", 2.0))

    current_settings = {
        "side": side,
        "mode": mode,
        "depth": depth,
        "time": thinking_time
    }

    command = [
        str(exe),
        "web",
        str(side),
        mode,
        str(depth),
        str(thinking_time)
    ]

    log = open(cpp_path("game_log.txt"), "w")

    game_process = subprocess.Popen(
        command,
        cwd=cpp_dir(),
        stdout=log,
        stderr=subprocess.STDOUT
    )

    time.sleep(0.3)

    return True, "Human game started."



def apply_random_opening(state, moves_count):
    moves_done = 0

    for _ in range(moves_count):
        legal = legal_indices(state)

        if len(legal) == 0:
            return True, 1 - state.player, moves_done

        move = live_rng.choice(legal)
        finished, winner = apply_move(state, move)
        moves_done += 1

        if finished:
            return True, winner, moves_done

    return False, None, moves_done


def start_live_match(settings):
    global active_mode, live_state, live_running, live_finished, live_winner
    global live_moves, live_last_step, live_last_move, live_last_bot, live_last_score
    global live_last_target, live_top_time, live_bottom_time, live_settings
    global live_neural_player, live_result_saved

    stop_game()
    clean_game_files()

    top_bot = str(settings.get("top_bot", "neural"))
    bottom_bot = str(settings.get("bottom_bot", "search"))

    if top_bot not in ["heuristic", "search", "neural"]:
        top_bot = "neural"

    if bottom_bot not in ["heuristic", "search", "neural"]:
        bottom_bot = "search"

    depth = int(settings.get("depth", 8))
    thinking_time = float(settings.get("time", 0.5))
    delay = 0.3
    max_moves = int(settings.get("max_moves", 400))

    live_settings = {
        "top_bot": top_bot,
        "bottom_bot": bottom_bot,
        "depth": depth,
        "time": thinking_time,
        "delay": delay,
        "max_moves": max_moves,
        "random_opening": live_random_opening
    }

    live_rng.seed(time.time_ns())
    live_state = reset_initial_state()

    opening_finished, opening_winner, opening_moves_done = apply_random_opening(
        live_state,
        live_random_opening
    )

    live_neural_player = None

    if top_bot == "neural" or bottom_bot == "neural":
        model_path = python_dir() / "saved_models" / "policy_model_v2.pth"
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        live_neural_player = NeuralPlayer(model_path, live_state.input_size, device)

    active_mode = "match"
    live_running = not opening_finished
    live_finished = opening_finished
    live_winner = opening_winner
    live_moves = opening_moves_done
    live_last_step = 0.0
    live_last_move = None
    live_last_bot = "random opening" if opening_moves_done > 0 else None
    live_last_score = 0.0
    live_last_target = live_state.current_vertex if opening_moves_done > 0 else None
    live_top_time = 0.0
    live_bottom_time = 0.0
    live_result_saved = False

    if opening_finished:
        append_live_result()

    return True, "Live bot match started."


def vertex_position(vertex):
    if 0 <= vertex < goal_width:
        x = (width - goal_width) / 2 + vertex
        y = -1

        return x, y

    bottom_start = goal_width + width * height

    if bottom_start <= vertex < bottom_start + goal_width:
        x = (width - goal_width) / 2 + (vertex - bottom_start)
        y = height

        return x, y

    index = vertex - goal_width
    x = index % width
    y = index // width

    return x, y


def read_status():
    path = cpp_path("web_status.txt")

    if not path.exists():
        return "waiting"

    return path.read_text().strip()


def process_alive():
    return game_process is not None and game_process.poll() is None


def choose_bot_move(state, bot):
    if bot == "heuristic":
        return best_heuristic_move(state)

    if bot == "neural":
        return live_neural_player.choose_move(state)

    if bot == "search":
        with contextlib.redirect_stdout(io.StringIO()):
            move, score = search_best_move_timed(
                state,
                max_depth=int(live_settings["depth"]),
                time_limit=float(live_settings["time"])
            )

        if move is None:
            move, score = best_heuristic_move(state)

        return move, score

    raise ValueError("Unknown bot: " + bot)


def append_live_result():
    global live_result_saved

    if live_result_saved:
        return

    output_dir = python_dir() / "evaluation_results"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "bot_match_results.csv"

    file_exists = output_path.exists()

    game_number = 1

    if file_exists:
        with open(output_path, "r", newline="") as file:
            game_number = max(sum(1 for _ in file) - 1, 0) + 1

    winner_side = "Draw"
    winner_bot = "Draw"

    if live_winner == 0:
        winner_side = "Top"
        winner_bot = live_settings["top_bot"]
    elif live_winner == 1:
        winner_side = "Bottom"
        winner_bot = live_settings["bottom_bot"]

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

    with open(output_path, "a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "game": game_number,
            "top_bot": live_settings["top_bot"],
            "bottom_bot": live_settings["bottom_bot"],
            "winner_side": winner_side,
            "winner_bot": winner_bot,
            "moves": live_moves,
            "reason": "live_match",
            "final_player": "Top" if live_state.player == 0 else "Bottom",
            "final_vertex": live_state.current_vertex,
            "opening_random": live_settings.get("random_opening", 0),
            "top_time": round(live_top_time, 4),
            "bottom_time": round(live_bottom_time, 4),
            "seed": ""
        })

    live_result_saved = True


def update_live_match(force=False):
    global live_running, live_finished, live_winner, live_moves, live_last_step
    global live_last_move, live_last_bot, live_last_score, live_last_target
    global live_top_time, live_bottom_time

    if active_mode != "match":
        return

    if live_state is None:
        return

    if live_finished:
        append_live_result()
        return

    if not live_running and not force:
        return

    now = time.time()

    if not force and now - live_last_step < float(live_settings["delay"]):
        return

    if live_moves >= int(live_settings["max_moves"]):
        live_running = False
        live_finished = True
        live_winner = None
        append_live_result()
        return

    legal = legal_indices(live_state)

    if len(legal) == 0:
        live_running = False
        live_finished = True
        live_winner = 1 - live_state.player
        append_live_result()
        return

    current_player = live_state.player
    current_bot = live_settings["top_bot"] if current_player == 0 else live_settings["bottom_bot"]

    start = time.time()

    move, score = choose_bot_move(live_state, current_bot)

    elapsed = time.time() - start

    if current_player == 0:
        live_top_time += elapsed
    else:
        live_bottom_time += elapsed

    if move is None:
        live_running = False
        live_finished = True
        live_winner = 1 - current_player
        append_live_result()
        return

    current_vertex = live_state.current_vertex
    target_vertex = int(live_state.neighbours[current_vertex, move].item())

    finished, winner = apply_move(live_state, move)

    live_moves += 1
    live_last_step = time.time()
    live_last_move = move
    live_last_bot = current_bot
    live_last_score = float(score)
    live_last_target = target_vertex

    if finished:
        live_running = False
        live_finished = True
        live_winner = winner
        append_live_result()


def state_to_data(state, status, settings, active, message=""):
    vertices = []
    edges = []

    for v in range(state.vertices_count):
        x, y = vertex_position(v)

        vertices.append({
            "id": v,
            "x": x,
            "y": y,
            "ball": v == state.current_vertex,
            "visited": bool(state.extra_turn[v].item())
        })

    for v in range(state.vertices_count):
        x1, y1 = vertex_position(v)

        for d in range(8):
            n = int(state.neighbours[v, d].item())

            if n < 0 or n < v:
                continue

            x2, y2 = vertex_position(n)
            used = not bool(state.allowed[v, d].item())

            edges.append({
                "from": v,
                "to": n,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "used": used
            })

    legal_moves = []
    legal = state.legal_moves()

    for move in range(8):
        if legal[move]:
            n = int(state.neighbours[state.current_vertex, move].item())
            x, y = vertex_position(n)

            legal_moves.append({
                "move": move,
                "target": n,
                "x": x,
                "y": y
            })

    data = {
        "ready": True,
        "active_mode": active,
        "player": state.player,
        "ball": state.current_vertex,
        "legal_count": len(legal_moves),
        "status": status,
        "vertices": vertices,
        "edges": edges,
        "legal_moves": legal_moves,
        "settings": settings,
        "message": message,
        "process_alive": process_alive()
    }

    if active == "match":
        winner_side = "None"
        winner_bot = "None"

        if live_winner == 0:
            winner_side = "Top"
            winner_bot = live_settings["top_bot"]
        elif live_winner == 1:
            winner_side = "Bottom"
            winner_bot = live_settings["bottom_bot"]
        elif live_finished:
            winner_side = "Draw"
            winner_bot = "Draw"

        data["match"] = {
            "moves": live_moves,
            "running": live_running,
            "finished": live_finished,
            "winner_side": winner_side,
            "winner_bot": winner_bot,
            "last_move": live_last_move,
            "last_move_name": direction_names[live_last_move] if live_last_move is not None else "-",
            "last_bot": live_last_bot if live_last_bot is not None else "-",
            "last_score": round(live_last_score, 4),
            "last_target": live_last_target if live_last_target is not None else "-",
            "top_time": round(live_top_time, 2),
            "bottom_time": round(live_bottom_time, 2)
        }

    return data


def get_human_state_data():
    state_path = cpp_path("gamestate.txt")

    if not state_path.exists():
        return {
            "ready": False,
            "active_mode": "human",
            "status": read_status(),
            "message": "No gamestate.txt yet. Start a new game.",
            "settings": current_settings,
            "process_alive": process_alive()
        }

    state = load_game_state(state_path)

    return state_to_data(
        state,
        read_status(),
        current_settings,
        "human"
    )


def get_state_data():
    with state_lock:
        if active_mode == "match":
            update_live_match()

            if live_state is None:
                return {
                    "ready": False,
                    "active_mode": "match",
                    "status": "waiting",
                    "message": "Start a live bot match.",
                    "settings": live_settings,
                    "process_alive": False
                }

            if live_finished:
                status = "match_finished"
            elif live_running:
                status = "match_running"
            else:
                status = "match_paused"

            return state_to_data(
                live_state,
                status,
                live_settings,
                "match"
            )

        return get_human_state_data()


html = """
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <title>Paper Soccer AI</title>
    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            background:
                radial-gradient(circle at top, #233044 0, #10131a 70%, #08090d 100%);
            color: #eeeeee;
            font-family: Arial, sans-serif;
        }

        .page {
            max-width: 1340px;
            margin: 18px auto;
            padding: 14px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            margin-bottom: 16px;
        }

        h1 {
            margin: 0;
            letter-spacing: 1px;
            font-size: 34px;
        }

        h2 {
            margin: 0 0 12px 0;
            font-size: 20px;
        }

        h3 {
            margin: 0 0 10px 0;
            color: #f2f5fb;
            font-size: 16px;
        }

        .subtitle {
            color: #aab2c0;
            margin-top: 6px;
        }

        .layout {
            display: grid;
            grid-template-columns: minmax(500px, 1fr) 240px 240px 260px;
            gap: 14px;
            align-items: stretch;
        }

        .board-column {
            display: flex;
            flex-direction: column;
        }

        .card {
            background: rgba(24, 28, 38, 0.94);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
        }

        .board-card {
            padding: 16px;
            height: 100%;
        }

        .panel {
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            height: 100%;
        }

        svg {
            width: 100%;
            background: #f7f7f2;
            border-radius: 14px;
            display: block;
        }

        .section-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 14px;
            flex: 1;
        }

        .section-card,
        .status-card {
            background: rgba(13, 17, 25, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 12px;
        }

        .section-card {
            min-height: 0;
        }

        .status-column {
            padding: 12px;
            height: 100%;
            overflow: auto;
        }

        .status-column .metric-grid {
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }

        .status-column .status-head {
            align-items: flex-start;
            flex-direction: column;
            gap: 8px;
        }

        .section-note {
            color: #9aa6b8;
            font-size: 12px;
            line-height: 1.4;
            margin-top: 10px;
        }

        .helper-card {
            padding: 12px;
            border-radius: 14px;
            background: rgba(13, 17, 25, 0.48);
            border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .helper-title {
            color: #f2f5fb;
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .legend-row {
            display: flex;
            align-items: center;
            gap: 9px;
            color: #aab2c0;
            font-size: 12px;
            line-height: 1.35;
            margin-top: 8px;
        }

        .legend-dot {
            width: 12px;
            height: 12px;
            border-radius: 999px;
            flex: 0 0 12px;
        }

        .legend-line {
            width: 18px;
            height: 4px;
            border-radius: 999px;
            flex: 0 0 18px;
            background: #111827;
        }

        .legend-red {
            background: #ef4444;
        }

        .legend-blue {
            background: #3b82f6;
        }

        .legend-green {
            background: rgba(34, 197, 94, 0.75);
            border: 2px solid #15803d;
        }

        .human-tip {
            margin-top: 12px;
            color: #8f9bad;
            font-size: 12px;
            line-height: 1.45;
        }

        label {
            display: block;
            margin-top: 8px;
            margin-bottom: 4px;
            color: #cbd3df;
            font-size: 11px;
        }

        select,
        input {
            width: 100%;
            padding: 8px 9px;
            border-radius: 10px;
            border: 1px solid #394150;
            background: #10141d;
            color: #f0f3f8;
            font-size: 13px;
            outline: none;
        }

        select:focus,
        input:focus {
            border-color: #60a5fa;
        }

        button {
            width: 100%;
            margin-top: 11px;
            padding: 10px 11px;
            border: 0;
            border-radius: 12px;
            background: #3ddc84;
            color: #06130c;
            font-size: 13px;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            filter: brightness(1.08);
        }

        .button-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-top: 10px;
        }

        .button-row button {
            margin-top: 0;
        }

        .secondary-button {
            background: #60a5fa;
            color: #07111f;
        }

        .danger-button {
            background: #f59e0b;
            color: #140b02;
        }

        .status-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
        }

        .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: #f59e0b;
            color: #111827;
            font-weight: bold;
            font-size: 12px;
        }

        .mode-chip {
            display: inline-block;
            padding: 5px 9px;
            border-radius: 999px;
            background: rgba(96, 165, 250, 0.16);
            color: #bfdbfe;
            font-size: 12px;
            border: 1px solid rgba(96, 165, 250, 0.25);
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }

        .metric {
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 11px;
            padding: 8px;
            min-height: 52px;
        }

        .metric-label {
            color: #8f9bad;
            font-size: 10px;
            margin-bottom: 4px;
        }

        .metric-value {
            color: #edf2fb;
            font-size: 13px;
            font-weight: bold;
            word-break: break-word;
        }

        .status-subtitle {
            margin-top: 12px;
            margin-bottom: 8px;
            color: #aab2c0;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .move-hit {
            cursor: pointer;
            fill: transparent;
            pointer-events: all;
        }

        .move-dot {
            pointer-events: none;
        }

        .move-group {
            cursor: pointer;
        }

        .move-group:hover .move-dot {
            opacity: 0.95;
        }

        .github-link {
            display: block;
            color: #9ec5ff;
            text-decoration: none;
            font-weight: bold;
            font-size: 14px;
        }

        .github-link:hover {
            color: #cfe2ff;
        }

        .error {
            color: #ffb4b4;
        }

        @media (max-width: 1180px) {
            .page {
                max-width: 760px;
                margin-left: auto;
                margin-right: auto;
            }

            .layout {
                grid-template-columns: minmax(0, 1fr);
                justify-items: center;
            }

            .board-column,
            .board-card,
            .panel,
            .status-column {
                width: 100%;
                max-width: 720px;
                margin-left: auto;
                margin-right: auto;
            }

            .status-column .metric-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        @media (max-width: 720px) {
            .page {
                padding: 12px;
                max-width: 100%;
            }

            h1 {
                font-size: 28px;
            }

            .section-grid,
            .metric-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>
    <div class="page">
        <div class="header">
            <div>
                <h1>Paper Soccer AI</h1>
                <div class="subtitle">Play manually or test the neural, search and heuristic bots</div>
            </div>
        </div>

        <div class="layout">
            <div class="board-column">
                <div class="card board-card">
                    <svg id="board" viewBox="0 0 720 900"></svg>
                </div>
            </div>

            <div class="card panel">
                <h2>Human game</h2>

                <div class="section-card column-section">
                    <h3>Human vs bot</h3>

                    <label>Your side</label>
                    <select id="side">
                        <option value="1">Bottom</option>
                        <option value="0">Top</option>
                    </select>

                    <label>Bot mode</label>
                    <select id="mode">
                        <option value="heuristic">Heuristic</option>
                        <option value="search" selected>Search</option>
                        <option value="neural">Neural</option>
                    </select>

                    <label>Search max depth</label>
                    <input id="humanDepth" type="number" min="1" max="12" value="8">

                    <label>Search thinking time [s]</label>
                    <input id="humanTime" type="number" min="0.1" max="30" step="0.1" value="2.0">

                    <button onclick="newGame()">Start human game</button>

                    <div class="section-note">
                        Click green targets during your turn to place the ball. Depth and time only affect the search bot.
                    </div>
                </div>

                <div class="helper-card">
                    <div class="helper-title">Board legend</div>

                    <div class="legend-row">
                        <span class="legend-dot legend-red"></span>
                        Ball position
                    </div>

                    <div class="legend-row">
                        <span class="legend-dot legend-green"></span>
                        Legal clickable target
                    </div>

                    <div class="legend-row">
                        <span class="legend-dot legend-blue"></span>
                        Bounce vertex
                    </div>
                </div>
                <a class="github-link" href="https://github.com/mikelsProject/paper-soccer-ai" target="_blank" rel="noreferrer">
                    View project on GitHub
                </a>
            </div>

            <div class="card panel">
                <h2>Live match</h2>

                <div class="section-card column-section">
                    <h3>Bot vs bot</h3>

                    <label>Top bot</label>
                    <select id="topBot">
                        <option value="neural" selected>Neural</option>
                        <option value="search">Search</option>
                        <option value="heuristic">Heuristic</option>
                    </select>

                    <label>Bottom bot</label>
                    <select id="bottomBot">
                        <option value="neural">Neural</option>
                        <option value="search" selected>Search</option>
                        <option value="heuristic">Heuristic</option>
                    </select>

                    <label>Search max depth</label>
                    <input id="matchDepth" type="number" min="1" max="12" value="8">

                    <label>Search thinking time [s]</label>
                    <input id="matchTime" type="number" min="0.1" max="30" step="0.1" value="0.5">

                    <label>Max moves</label>
                    <input id="maxMoves" type="number" min="20" max="1000" value="400">

                    <button onclick="startMatch()">Start live bot match</button>

                    <div class="button-row">
                        <button class="secondary-button" onclick="pauseMatch()">Pause</button>
                        <button class="secondary-button" onclick="resumeMatch()">Resume</button>
                    </div>

                    <button class="danger-button" onclick="stepMatch()">One step</button>

                    <div class="section-note">
                        Live view uses a fixed display pause of 0.3 s between moves. Search time only affects search bots.
                    </div>
                </div>
            </div>

            <div id="info" class="card status-card status-column"></div>
        </div>
    </div>

    <script>
        const scale = 54;
        const marginX = 90;
        const marginY = 95;

        function px(x) {
            return marginX + x * scale;
        }

        function py(y) {
            return marginY + (y + 1) * scale;
        }

        function el(name, attrs) {
            const e = document.createElementNS("http://www.w3.org/2000/svg", name);

            for (const key in attrs) {
                e.setAttribute(key, attrs[key]);
            }

            return e;
        }

        function isGoalGuideEdge(edge) {
            const touchesGoal = edge.y1 < 0 || edge.y2 < 0 || edge.y1 > 12 || edge.y2 > 12;

            return touchesGoal && !edge.used;
        }

        async function postJSON(path, payload) {
            const response = await fetch(path, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            return await response.json();
        }

        async function newGame() {
            const payload = {
                side: Number(document.getElementById("side").value),
                mode: document.getElementById("mode").value,
                depth: Number(document.getElementById("humanDepth").value),
                time: Number(document.getElementById("humanTime").value)
            };

            const data = await postJSON("/new-game", payload);

            if (!data.ok) {
                document.getElementById("info").innerHTML =
                    "<span class='error'>" + data.message + "</span>";
            }

            await loadBoard();
        }

        async function startMatch() {
            const payload = {
                top_bot: document.getElementById("topBot").value,
                bottom_bot: document.getElementById("bottomBot").value,
                depth: Number(document.getElementById("matchDepth").value),
                time: Number(document.getElementById("matchTime").value),
                max_moves: Number(document.getElementById("maxMoves").value)
            };

            const data = await postJSON("/start-match", payload);

            if (!data.ok) {
                document.getElementById("info").innerHTML =
                    "<span class='error'>" + data.message + "</span>";
            }

            await loadBoard();
        }

        async function pauseMatch() {
            await postJSON("/pause-match", {});
            await loadBoard();
        }

        async function resumeMatch() {
            await postJSON("/resume-match", {});
            await loadBoard();
        }

        async function stepMatch() {
            await postJSON("/step-match", {});
            await loadBoard();
        }

        async function sendMove(move) {
            await postJSON("/move", {move: move});
        }

        function statusText(status) {
            if (status === "human") return "Your move";
            if (status === "bot") return "Bot is thinking";
            if (status === "match_running") return "Live bot match";
            if (status === "match_paused") return "Bot match paused";
            if (status === "match_finished") return "Bot match finished";
            if (status.startsWith("gameover_")) return "Game over - " + status.replace("gameover_", "") + " won";
            if (status === "gameover") return "Game over";
            if (status === "waiting") return "Waiting";
            if (status === "executable_not_found") return "soccer.exe not found";

            return status;
        }

        function metric(label, value) {
            return "<div class='metric'>" +
                "<div class='metric-label'>" + label + "</div>" +
                "<div class='metric-value'>" + value + "</div>" +
                "</div>";
        }

        function drawLegalMoves(svg, data) {
            const showMoves =
                data.status === "human" ||
                data.status === "match_running" ||
                data.status === "match_paused";

            if (!showMoves) {
                return;
            }

            for (const m of data.legal_moves) {
                const g = el("g", {
                    class: "move-group"
                });

                const hit = el("circle", {
                    cx: px(m.x),
                    cy: py(m.y),
                    r: 34,
                    class: "move-hit"
                });

                const dot = el("circle", {
                    cx: px(m.x),
                    cy: py(m.y),
                    r: data.status === "human" ? 15 : 10,
                    fill: data.status === "human" ? "rgba(34, 197, 94, 0.55)" : "rgba(245, 158, 11, 0.55)",
                    stroke: data.status === "human" ? "#15803d" : "#b45309",
                    "stroke-width": 2,
                    class: "move-dot"
                });

                if (data.status === "human") {
                    g.onclick = () => sendMove(m.move);
                }

                g.appendChild(hit);
                g.appendChild(dot);
                svg.appendChild(g);
            }
        }

        function makeInfo(data) {
            let playerName = data.player === 0 ? "Top" : "Bottom";

            if (data.active_mode === "match") {
                let match = data.match;

                let html = "<div class='status-head'>" +
                    "<span class='pill'>" + statusText(data.status) + "</span>" +
                    "<span class='mode-chip'>" + data.settings.top_bot + " vs " + data.settings.bottom_bot + "</span>" +
                    "</div>";

                html += "<div class='metric-grid'>" +
                    metric("Player to move", playerName) +
                    metric("Ball vertex", data.ball) +
                    metric("Legal moves", data.legal_count) +
                    metric("Moves played", match.moves) +
                    metric("Last bot", match.last_bot) +
                    metric("Last move", match.last_move_name + " " + match.last_target) +
                    "</div>";

                html += "<div class='status-subtitle'>Match result</div>";

                html += "<div class='metric-grid'>" +
                    metric("Winner side", match.winner_side) +
                    metric("Winner bot", match.winner_bot) +
                    metric("Last score", match.last_score) +
                    metric("Search", "d" + data.settings.depth + ", " + data.settings.time + " s") +
                    metric("Top time", match.top_time + " s") +
                    metric("Bottom time", match.bottom_time + " s") +
                    "</div>";

                return html;
            }

            let sideName = data.settings.side === 0 ? "Top" : "Bottom";

            let html = "<div class='status-head'>" +
                "<span class='pill'>" + statusText(data.status) + "</span>" +
                "<span class='mode-chip'>Human vs " + data.settings.mode + "</span>" +
                "</div>";

            html += "<div class='metric-grid'>" +
                metric("Your side", sideName) +
                metric("Bot", data.settings.mode) +
                metric("Player to move", playerName) +
                metric("Ball vertex", data.ball) +
                metric("Legal moves", data.legal_count) +
                metric("Search", "d" + data.settings.depth + ", " + data.settings.time + " s") +
                "</div>";

            return html;
        }

        async function loadBoard() {
            const response = await fetch("/state");
            const data = await response.json();

            const svg = document.getElementById("board");
            svg.innerHTML = "";

            if (!data.ready) {
                document.getElementById("info").innerHTML =
                    "<div class='status-head'><span class='pill'>" + statusText(data.status) + "</span></div>" +
                    "<div class='section-note'>" + data.message + "</div>";
                return;
            }

            for (const edge of data.edges) {
                if (isGoalGuideEdge(edge)) {
                    continue;
                }

                svg.appendChild(el("line", {
                    x1: px(edge.x1),
                    y1: py(edge.y1),
                    x2: px(edge.x2),
                    y2: py(edge.y2),
                    stroke: edge.used ? "#111827" : "#c8ccd2",
                    "stroke-width": edge.used ? 4 : 1.2,
                    "stroke-linecap": "round"
                }));
            }

            for (const v of data.vertices) {
                let color = "#555";
                let r = 4;

                if (v.visited) {
                    color = "#3b82f6";
                    r = 6;
                }

                if (v.ball) {
                    color = "#ef4444";
                    r = 13;
                }

                svg.appendChild(el("circle", {
                    cx: px(v.x),
                    cy: py(v.y),
                    r: r,
                    fill: color
                }));
            }

            drawLegalMoves(svg, data);

            document.getElementById("info").innerHTML = makeInfo(data);
        }

        loadBoard();
        setInterval(loadBoard, 350);
    </script>
</body>

</html>
"""



class Handler(BaseHTTPRequestHandler):
    def send_json(self, data):
        body = json.dumps(data)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if self.path == "/state":
            self.send_json(get_state_data())
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        global live_running

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body.decode("utf-8")) if body else {}

        if self.path == "/new-game":
            with state_lock:
                ok, message = start_game(data)

            self.send_json({"ok": ok, "message": message})
            return

        if self.path == "/start-match":
            try:
                with state_lock:
                    ok, message = start_live_match(data)

                self.send_json({"ok": ok, "message": message})
            except Exception as error:
                self.send_json({"ok": False, "message": str(error)})

            return

        if self.path == "/pause-match":
            with state_lock:
                live_running = False

            self.send_json({"ok": True})
            return

        if self.path == "/resume-match":
            with state_lock:
                if active_mode == "match" and not live_finished:
                    live_running = True

            self.send_json({"ok": True})
            return

        if self.path == "/step-match":
            with state_lock:
                update_live_match(force=True)

            self.send_json({"ok": True})
            return

        if self.path == "/move":
            move = int(data["move"])
            cpp_path("web_move.txt").write_text(str(move))
            self.send_json({"ok": True})
            return

        self.send_response(404)
        self.end_headers()


def main():
    port = 8000

    try:
        server = ThreadingHTTPServer(("localhost", port), Handler)
    except PermissionError:
        port = 8080
        server = ThreadingHTTPServer(("localhost", port), Handler)

    print(f"Open: http://localhost:{port}")
    print("Use the game panel to start human games or live bot matches.")
    server.serve_forever()


if __name__ == "__main__":
    main()
