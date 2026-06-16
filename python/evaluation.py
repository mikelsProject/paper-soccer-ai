direction_names = [
    "up",
    "up-right",
    "right",
    "down-right",
    "down",
    "down-left",
    "left",
    "up-left"
]


width = 11
height = 13


def goal_width_from_state(state):
    return (state.vertices_count - width * height) // 2


def is_top_goal(state, vertex):
    goal_width = goal_width_from_state(state)

    return 0 <= vertex < goal_width


def is_bottom_goal(state, vertex):
    goal_width = goal_width_from_state(state)
    bottom_goal_start = goal_width + width * height

    return bottom_goal_start <= vertex < bottom_goal_start + goal_width


def vertex_y(state, vertex):
    goal_width = goal_width_from_state(state)

    if is_top_goal(state, vertex):
        return -1

    if is_bottom_goal(state, vertex):
        return height

    return (vertex - goal_width) // width


def goal_progress(state, vertex): # towards goal
    player = state.player

    if player == 0:
        if is_bottom_goal(state, vertex):
            return 1.0
        if is_top_goal(state, vertex):
            return -1.0
        
        return vertex_y(state, vertex) / (height - 1)

    if player == 1:
        if is_top_goal(state, vertex):
            return 1.0
        if is_bottom_goal(state, vertex):
            return -1.0
        return (height - 1 - vertex_y(state, vertex)) / (height - 1)

    return 0.0


def mobility_score(state, vertex):
    if vertex < 0:
        return 0.0

    return state.allowed[vertex].sum().item() / 8.0


def evaluate_vertex(state, vertex):
    if vertex < 0:
        return -100.0

    progress = goal_progress(state, vertex)
    mobility = mobility_score(state, vertex)

    trap_penalty = 0.0

    if mobility == 0: # adding some penalty if the move leads to a trapped position
        trap_penalty = 5.0
    elif mobility <= 0.125:
        trap_penalty = 3.0

    score = 5.0 * progress + (2.0 * mobility) - trap_penalty # equation for the score

    return score


def evaluate_move(state, move):
    current = state.current_vertex

    if not state.allowed[current, move].bool(): # not an allowed state
        return -100.0

    next_vertex = int(state.neighbours[current, move].item())

    return evaluate_vertex(state, next_vertex)


def best_heuristic_move(state): # this function returns the best move and its score
    current = state.current_vertex

    best_move = None
    best_score = -1.0e9

    for move in range(8): # checking all possible moves
        if not state.allowed[current, move].bool():
            continue

        score = evaluate_move(state, move)

        if score > best_score: # new best score
            best_score = score
            best_move = move

    return best_move, best_score


def print_move_scores(state):
    current = state.current_vertex

    for move in range(8):
        if not state.allowed[current, move].bool():
            continue

        next_vertex = int(state.neighbours[current, move].item())
        score = evaluate_move(state, move)

        print(move, direction_names[move], ": ", next_vertex, "score:", round(score, 4))