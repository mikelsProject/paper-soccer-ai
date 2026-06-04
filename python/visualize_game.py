from pathlib import Path

from parse import load_game_state


width = 11
height = 13
goal_width = 5


def project_root():
    return Path(__file__).resolve().parent.parent


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


def edge_used(state, vertex, direction):
    if state.neighbours[vertex, direction] < 0:
        return False

    return not bool(state.allowed[vertex, direction].item())


def generate_html(state):
    scale = 55
    margin = 80

    canvas_width = int((width - 1) * scale + 2 * margin)
    canvas_height = int((height + 1) * scale + 2 * margin)

    ball = state.current_vertex

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Paper Soccer AI Board</title>
    <style>
        body {{
            background: #111;
            color: #eee;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            padding: 30px;
        }}

        .container {{
            background: #1b1b1b;
            padding: 25px;
            border-radius: 18px;
            box-shadow: 0 0 30px rgba(0,0,0,0.4);
        }}

        h1 {{
            margin-top: 0;
            font-size: 24px;
        }}

        svg {{
            background: #f7f7f7;
            border-radius: 14px;
        }}

        .info {{
            margin-top: 15px;
            color: #ccc;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Paper Soccer AI</h1>

        <svg width="{canvas_width}" height="{canvas_height}">
"""

    for y in range(height):
        for x in range(width):
            px = margin + x * scale
            py = margin + (y + 1) * scale

            html += f'<circle cx="{px}" cy="{py}" r="4" fill="#888" />\n'

    for v in range(state.vertices_count):
        x1, y1 = vertex_position(v)
        px1 = margin + x1 * scale
        py1 = margin + (y1 + 1) * scale

        for d in range(8):
            n = int(state.neighbours[v, d].item())

            if n < 0:
                continue

            if n < v:
                continue

            x2, y2 = vertex_position(n)
            px2 = margin + x2 * scale
            py2 = margin + (y2 + 1) * scale

            if edge_used(state, v, d):
                color = "#222"
                stroke_width = 4
            else:
                color = "#d0d0d0"
                stroke_width = 1

            html += f'<line x1="{px1}" y1="{py1}" x2="{px2}" y2="{py2}" stroke="{color}" stroke-width="{stroke_width}" />\n'

    for v in range(state.vertices_count):
        x, y = vertex_position(v)
        px = margin + x * scale
        py = margin + (y + 1) * scale

        if v == ball:
            html += f'<circle cx="{px}" cy="{py}" r="13" fill="#e63946" />\n'
        elif state.extra_turn[v].item() == 1:
            html += f'<circle cx="{px}" cy="{py}" r="6" fill="#457b9d" />\n'
        else:
            html += f'<circle cx="{px}" cy="{py}" r="4" fill="#555" />\n'

    html += f"""
        </svg>

        <div class="info">
            Player to move: {state.player}<br>
            Ball vertex: {state.current_vertex}<br>
            Legal moves: {int(state.legal_moves().sum().item())}
        </div>
    </div>
</body>
</html>
"""

    return html


def main():
    state_path = project_root() / "cpp" / "gamestate.txt"
    output_path = project_root() / "python" / "board.html"

    state = load_game_state(state_path)
    html = generate_html(state)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html)

    print("Saved board visualization to:", output_path)


if __name__ == "__main__":
    main()