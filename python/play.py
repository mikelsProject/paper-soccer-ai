def choose_move(model, state, legal_moves):
    model.eval()

    with torch.no_grad():
        scores = model(state)

    legal_moves = torch.tensor(legal_moves, dtype=torch.bool, device=scores.device)

    masked_scores = scores.clone()
    masked_scores[:, ~legal_moves] = float("-inf")

    move = masked_scores.argmax(dim=1).item()

    return move