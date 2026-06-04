from dataclasses import replace
from evaluation import evaluate_vertex, is_top_goal, is_bottom_goal, direction_names

import time


opposite_direction = { # mapping each direction to its opposite direction so we can mark the opposite edge as not allowed when we apply a move
    0: 4,
    1: 5,
    2: 6,
    3: 7,
    4: 0,
    5: 1,
    6: 2,
    7: 3
}


def clone_state(state): # creating a deep copy of the state so we can modify it without affecting the original state during the search
    return replace(
        state,
        ball=state.ball.clone(),
        allowed=state.allowed.clone(),
        extra_turn=state.extra_turn.clone(),
        neighbours=state.neighbours.clone()
    )


def other_player(player):
    if player == 0:
        return 1

    return 0


def set_ball(state, vertex):
    state.ball.zero_()
    state.ball[vertex] = 1.0


def legal_indices(state):
    legal = state.legal_moves()

    return [move for move in range(8) if legal[move]]


def winner_after_move(state, vertex):
    if is_top_goal(state, vertex):
        return 1

    if is_bottom_goal(state, vertex):
        return 0

    return None


def is_dead_end(state, vertex):
    return int(state.allowed[vertex].sum().item()) == 0


def apply_move(state, move): # applying a move to the state and returning whether the game is finished and who the winner is (if there is one winner)
    current = state.current_vertex

    if not state.allowed[current, move].bool():
        return True, other_player(state.player)

    next_vertex = int(state.neighbours[current, move].item())

    state.allowed[current, move] = 0.0 # marking the edge as not allowed

    opposite = opposite_direction[move] # marking the opposite edge as not allowed in the next vertex because it's an undirected graph and we can't go back through the same edge

    if next_vertex >= 0: # if the next vertex is valid (not -1)
        state.allowed[next_vertex, opposite] = 0.0

    set_ball(state, next_vertex)

    winner = winner_after_move(state, next_vertex)

    if winner is not None:
        return True, winner

    if is_dead_end(state, next_vertex):
        return True, other_player(state.player)

    if not state.extra_turn[next_vertex].bool():
        state.player = other_player(state.player)

    state.extra_turn[next_vertex] = 1.0 # marking that we have an extra turn in the next vertex so if we end up there again we know that we do not switch players

    return False, None


def state_key(state): # creating a unique key for the state so we can store it in a transposition table to avoid recalculating the exactly same state multiple times during the search
    return (
        state.player,
        state.current_vertex,
        tuple(state.allowed.flatten().int().tolist()),
        tuple(state.extra_turn.int().tolist())
    )


def evaluate_state_for_current_player(state):
    return evaluate_vertex(state, state.current_vertex)


def terminal_value(winner, player): # win is a 1000
    if winner == player:
        return 1000.0

    return -1000.0


def negamax(state, depth, alpha, beta, table): # negamax search algorithm with alpha-beta pruning and a transposition table to store previously evaluated states to speed up the search
    key = (state_key(state), depth)

    if key in table:
        return table[key]

    moves = legal_indices(state)

    if len(moves) == 0: # if there are no legal moves, it's a loss for the current player
        value = -1000.0
        table[key] = value
        return value

    if depth == 0: # only if depth is = 0
        value = evaluate_state_for_current_player(state)
        table[key] = value
        return value

    best_value = -1.0e9
    current_player = state.player

    ordered_moves = order_moves(state, moves) # ordering moves based on a heuristic evaluation of the resulting state after applying the move

    for move in ordered_moves: # applying each move, recursively calling negamax to evaluate the state
        child = clone_state(state)

        finished, winner = apply_move(child, move)

        if finished: # if the game is finished after applying the move, we return the terminal value for the winner
            value = terminal_value(winner, current_player)
        else:
            if child.player == current_player: # if the player to move in the child state is the same as the current player, we call negamax with the same alpha and beta values
                value = negamax(child, depth - 1, alpha, beta, table)
            else:
                value = -negamax(child, depth - 1, -beta, -alpha, table) # if the player to move in the child state is the opponent, we call negamax with the alpha and beta values negated and swapped

        if value > best_value: # if the value returned from the recursive call is better we update it as some best value
            best_value = value

        alpha = max(alpha, value)

        if alpha >= beta:
            break

    table[key] = best_value
    return best_value


def order_moves(state, moves): # ordering moves based on a heuristic evaluation
    scored = []

    for move in moves:
        child = clone_state(state)
        finished, winner = apply_move(child, move)

        if finished:
            if winner == state.player:
                score = 1000.0
            else:
                score = -1000.0
        else:
            score = evaluate_state_for_current_player(child)

        scored.append((move, score))

    scored.sort(key=lambda x: x[1], reverse=True) # sorting moves by score in descending order so we search the most promising (best) moves first

    return [move for move, score in scored]


def search_best_move(state, depth=7): # searching for the best move using the negamax search algorithm with alpha-beta pruning
    moves = legal_indices(state)

    if len(moves) == 0: # if there are no legal moves, we return None and a very low score because it is a loss for the current player
        return None, -1000.0

    best_move = None
    best_value = -1.0e9

    table = {}

    ordered_moves = order_moves(state, moves)

    for move in ordered_moves: # applying each move, recursively calling negamax to evaluate the state
        child = clone_state(state)

        finished, winner = apply_move(child, move)

        if finished:
            value = terminal_value(winner, state.player)
        else:
            if child.player == state.player:
                value = negamax(child, depth - 1, -1.0e9, 1.0e9, table)
            else:
                value = -negamax(child, depth - 1, -1.0e9, 1.0e9, table)

        print("search", move, direction_names[move], "value:", round(value, 4))

        if value > best_value:
            best_value = value
            best_move = move

    return best_move, best_value

def search_best_move_timed(state, max_depth=10, time_limit=3.0):
    start_time = time.time()

    best_move = None
    best_value = -1.0e9

    for depth in range(1, max_depth + 1):
        elapsed = time.time() - start_time # elapsed time so we can pick a maximum

        if elapsed >= time_limit:
            break

        print()
        print("Searching depth:", depth)

        move, value = search_best_move(state, depth=depth)

        elapsed = time.time() - start_time

        if elapsed >= time_limit:
            print("time limit reached after depth:", depth)
            break

        if move is not None:
            best_move = move
            best_value = value

        print(
            "Completed depth:",
            depth,
            "best move:",
            best_move,
            "value:",
            round(best_value, 4),
            "time:",
            round(elapsed, 2),
            "s"
        )

    return best_move, best_value