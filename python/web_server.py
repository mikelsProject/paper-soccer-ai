from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json
import subprocess
import sys
import time

from parse import load_game_state


width = 11
height = 13
goal_width = 5
game_process = None
current_settings = {
    "side": 1,
    "mode": "search",
    "depth": 8,
    "time": 2.0
}


def project_root():
    return Path(__file__).resolve().parent.parent


def cpp_dir():
    return project_root() / "cpp"


def cpp_path(name):
    return cpp_dir() / name


def find_executable():
    candidates = [
        cpp_dir() / "build" / "soccer.exe",
        project_root() / "build" / "soccer.exe",
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


def start_game(settings):
    global game_process, current_settings

    stop_game()
    clean_game_files()

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

    return True, "Game started."


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


def get_state_data():
    state_path = cpp_path("gamestate.txt")

    if not state_path.exists():
        return {
            "ready": False,
            "status": read_status(),
            "message": "No gamestate.txt yet. Start a new game.",
            "settings": current_settings,
            "process_alive": process_alive()
        }

    state = load_game_state(state_path)

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

    return {
        "ready": True,
        "player": state.player,
        "ball": state.current_vertex,
        "legal_count": len(legal_moves),
        "status": read_status(),
        "vertices": vertices,
        "edges": edges,
        "legal_moves": legal_moves,
        "settings": current_settings,
        "process_alive": process_alive()
    }


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
            max-width: 1100px;
            margin: 24px auto;
            padding: 20px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: center;
            margin-bottom: 18px;
        }

        h1 {
            margin: 0;
            letter-spacing: 1px;
            font-size: 34px;
        }

        .subtitle {
            color: #aab2c0;
            margin-top: 6px;
        }

        .layout {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 310px;
            gap: 18px;
            align-items: stretch;
        }

        .card {
            background: rgba(24, 28, 38, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.28);
        }

        .board-card {
            padding: 16px;
            min-height: 908px;
        }

        .panel {
            padding: 18px;
            min-height: 908px;
            display: flex;
            flex-direction: column;
        }

        svg {
            width: 100%;
            background: #f7f7f2;
            border-radius: 14px;
            display: block;
        }

        .panel-content {
            flex: 1;
        }

        label {
            display: block;
            margin-top: 14px;
            margin-bottom: 6px;
            color: #cbd3df;
            font-size: 14px;
        }

        select,
        input {
            width: 100%;
            padding: 10px 12px;
            border-radius: 10px;
            border: 1px solid #394150;
            background: #10141d;
            color: #f0f3f8;
            font-size: 15px;
        }

        button {
            width: 100%;
            margin-top: 40px;
            padding: 12px 14px;
            border: 0;
            border-radius: 12px;
            background: #3ddc84;
            color: #06130c;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            filter: brightness(1.08);
        }

        .info {
            margin-top: 18px;
            line-height: 1.6;
            font-size: 15px;
            color: #dbe2ec;
        }

        .pill {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 10px;
            background: orange;
            color: #dbe8ff;
            margin-top: 6px;
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

        .hint {
            color: #9aa6b8;
            font-size: 13px;
            line-height: 1.45;
            margin-top: 12px;
        }

        .github-link {
            display: block;
            margin-top: auto;
            padding-top: 18px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
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

        @media (max-width: 900px) {
            .layout {
                grid-template-columns: 1fr;
            }

            .board-card,
            .panel {
                min-height: auto;
            }

            .panel {
                position: static;
            }
        }
    </style>
</head>

<body>
    <div class="page">
        <div class="header">
            <div>
                <h1>Paper Soccer AI</h1>
                <div class="subtitle">Play against neural bot, heuristic or search algorithm</div>
            </div>
        </div>

        <div class="layout">
            <div class="card board-card">
                <svg id="board" viewBox="0 0 720 900"></svg>
            </div>

            <div class="card panel">
                <div class="panel-content">
                    <h2>New game</h2>

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
                    <input id="depth" type="number" min="1" max="12" value="8">

                    <label>Search thinking time [s]</label>
                    <input id="time" type="number" min="0.2" max="30" step="0.1" value="2.0">

                    <button onclick="newGame()">Start new game</button>

                    <div class="hint">
                        Thinking time only changes the search bot. Heuristic and neural modes are almost instant.
                        <br><br>
                        During your turn, click the green target where you want to place the ball.
                    </div>

                    <div class="info" id="info"></div>
                </div>

                <a class="github-link" href="https://github.com/mikelsProject/paper-soccer-ai" target="_blank" rel="noreferrer">
                    View project on GitHub
                </a>
            </div>
        </div>
    </div>

    <script>
        const scale = 55;
        const margin = 80;

        function px(x) {
            return margin + x * scale;
        }

        function py(y) {
            return margin + (y + 1) * scale;
        }

        function el(name, attrs) {
            const e = document.createElementNS("http://www.w3.org/2000/svg", name);

            for (const key in attrs) {
                e.setAttribute(key, attrs[key]);
            }

            return e;
        }

        async function newGame() {
            const payload = {
                side: Number(document.getElementById("side").value),
                mode: document.getElementById("mode").value,
                depth: Number(document.getElementById("depth").value),
                time: Number(document.getElementById("time").value)
            };

            const response = await fetch("/new-game", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!data.ok) {
                document.getElementById("info").innerHTML =
                    "<span class='error'>" + data.message + "</span>";
            }

            await loadBoard();
        }

        async function sendMove(move) {
            await fetch("/move", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({move: move})
            });
        }

        function statusText(status) {
            if (status === "human") return "Your move";
            if (status === "bot") return "Bot is thinking";
            if (status.startsWith("gameover_")) return "Game over - " + status.replace("gameover_", "") + " won";
            if (status === "gameover") return "Game over";
            if (status === "waiting") return "Waiting for a new game";
            if (status === "executable_not_found") return "soccer.exe not found";
            return status;
        }

        async function loadBoard() {
            const response = await fetch("/state");
            const data = await response.json();

            const svg = document.getElementById("board");
            svg.innerHTML = "";

            if (!data.ready) {
                document.getElementById("info").innerHTML =
                    "<span class='pill'>" + statusText(data.status) + "</span><br>" +
                    data.message;
                return;
            }

            for (const edge of data.edges) {
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

            if (data.status === "human") {
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
                        r: 15,
                        fill: "rgba(34, 197, 94, 0.55)",
                        stroke: "#15803d",
                        "stroke-width": 2,
                        class: "move-dot"
                    });

                    g.onclick = () => sendMove(m.move);
                    g.appendChild(hit);
                    g.appendChild(dot);
                    svg.appendChild(g);
                }
            }

            let playerName = data.player === 0 ? "Top" : "Bottom";
            let sideName = data.settings.side === 0 ? "Top" : "Bottom";

            document.getElementById("info").innerHTML =
                "<span class='pill'>" + statusText(data.status) + "</span><br><br>" +
                "You: " + sideName + "<br>" +
                "Bot: " + data.settings.mode + "<br>" +
                "Search: depth " + data.settings.depth + ", " + data.settings.time + " s<br><br>" +
                "Player to move: " + playerName + "<br>" +
                "Ball vertex: " + data.ball + "<br>" +
                "Legal moves: " + data.legal_count;
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
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if self.path == "/new-game":
            data = json.loads(body.decode("utf-8")) if body else {}
            ok, message = start_game(data)
            self.send_json({"ok": ok, "message": message})
            return

        if self.path == "/move":
            data = json.loads(body.decode("utf-8"))
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
    print("Use the game panel to start/restart games.")
    server.serve_forever()


if __name__ == "__main__":
    main()
