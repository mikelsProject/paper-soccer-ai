from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json

from parse import load_game_state


width = 11
height = 13
goal_width = 5


def project_root():
    return Path(__file__).resolve().parent.parent


def cpp_path(name):
    return project_root() / "cpp" / name


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


def get_state_data():
    state = load_game_state(cpp_path("gamestate.txt"))

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

        for d in range(8): # 8 directions
            n = int(state.neighbours[v, d].item())

            if n < 0 or n < v: # ignore invalid and already processed edges
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
        "player": state.player,
        "ball": state.current_vertex,
        "legal_count": len(legal_moves),
        "status": read_status(),
        "vertices": vertices,
        "edges": edges,
        "legal_moves": legal_moves
    }


html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Paper Soccer AI</title>
    <style>
        body {
            margin: 0;
            background: #101010;
            color: #eeeeee;
            font-family: Arial, sans-serif;
        }

        .page {
            max-width: 1100px;
            margin: 25px auto;
            padding: 25px;
            background: #181818;
            border-radius: 18px;
        }

        h1 {
            margin-top: 0;
            letter-spacing: 1px;
        }

        svg {
            width: 100%;
            background: #f4f4f4;
            border-radius: 14px;
        }

        .info {
            margin-top: 16px;
            font-size: 18px;
            line-height: 1.5;
        }

        .move {
            cursor: pointer;
        }

        .move:hover {
            opacity: 0.7;
        }
    </style>
</head>
<body>
    <div class="page">
        <h1>Paper Soccer AI</h1>
        <svg id="board" viewBox="0 0 720 900"></svg>
        <div class="info" id="info"></div>
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

        async function sendMove(move) {
            await fetch("/move", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({move: move})
            });
        }

        async function loadBoard() {
            const response = await fetch("/state");
            const data = await response.json();

            const svg = document.getElementById("board");
            svg.innerHTML = "";

            for (const edge of data.edges) {
                svg.appendChild(el("line", {
                    x1: px(edge.x1),
                    y1: py(edge.y1),
                    x2: px(edge.x2),
                    y2: py(edge.y2),
                    stroke: edge.used ? "#222" : "#cccccc",
                    "stroke-width": edge.used ? 4 : 1
                }));
            }

            for (const v of data.vertices) {
                let color = "#555";
                let r = 4;

                if (v.visited) {
                    color = "#457b9d";
                    r = 6;
                }

                if (v.ball) {
                    color = "#e63946";
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
                    const c = el("circle", {
                        cx: px(m.x),
                        cy: py(m.y),
                        r: 18,
                        fill: "rgba(46, 204, 113, 0.45)",
                        class: "move"
                    });

                    c.onclick = () => sendMove(m.move);
                    svg.appendChild(c);
                }
            }

            let playerName = data.player === 0 ? "Top" : "Bottom";

            document.getElementById("info").innerHTML =
                "Status: " + data.status + "<br>" +
                "Player to move: " + playerName + "<br>" +
                "Ball vertex: " + data.ball + "<br>" +
                "Legal moves: " + data.legal_count;
        }

        loadBoard();
        setInterval(loadBoard, 500);
    </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if self.path == "/state":
            data = get_state_data()
            body = json.dumps(data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/move":
            self.send_response(404)
            self.end_headers()

            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body.decode("utf-8"))

        move = int(data["move"])
        cpp_path("web_move.txt").write_text(str(move))

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")


def main():
    server = ThreadingHTTPServer(("localhost", 5000), Handler)
    print("Open: http://localhost:5000")
    server.serve_forever()


if __name__ == "__main__":
    main()