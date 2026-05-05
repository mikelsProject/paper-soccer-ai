# Paper Soccer Neural Network

## Overview

This project is created for the **Applied Machine Learning** course.
The goal of the project is to build an intelligent system capable of playing the classic **paper-soccer game** using machine learning techniques.

Paper soccer is a simple strategic game usually played on a sheet of paper with a grid, two goals, and a ball represented by a point. Even though the rules are quite simple, the game can become surprisingly complex because each move changes the available paths, blocks future moves, and may force the opponent into difficult positions.

In this project, we want to create a neural-network-based player that can understand the current state of the game, evaluate positions, choose moves, and eventually improve by playing games against itself.

The project will include multiple gameplay options, such as:

- Human vs human
- Human vs neural network
- Neural network vs neural network
- Self-play training
- Position evaluation
- Move suggestion
- Game simulation and analysis

The main idea is to treat paper soccer as a decision-making problem, where the model receives the current board state and tries to choose the best possible move.

---

# Table of Contents

1. [What Is Paper Soccer?](#what-is-paper-soccer)
2. [Rules of the Game](#rules-of-the-game)
3. [Project Goal](#project-goal)
4. [Machine Learning Idea](#machine-learning-idea)
5. [Game Representation](#game-representation)
6. [Planned Features](#planned-features)
7. [Neural Network Player](#neural-network-player)
8. [Self-Play](#self-play)
9. [Position Evaluation](#position-evaluation)
10. [Possible Project Structure](#possible-project-structure)
11. [Technologies](#technologies)
12. [Challenges](#challenges)
13. [Future Improvements](#future-improvements)
14. [Authors](#authors)

---

# What Is Paper Soccer?

Paper soccer is a two-player pencil-and-paper game. It is usually played on a rectangular grid that represents a football field. The field has two goals, one at the top and one at the bottom. The ball starts in the center of the field.

Players take turns drawing lines from one grid point to another. Each line represents the movement of the ball. The goal of the game is to move the ball into the opponent's goal.

Although the game looks very simple, it contains many strategic elements:

- Players can block paths.
- Players can force the opponent into dead ends.
- Some moves allow the same player to move again.
- The position of the ball and already drawn lines strongly affects future possibilities.
- The game can be analyzed similarly to other board games, such as chess or checkers.

Because of this, paper soccer is an interesting game for a machine learning project.

---

# Rules of the Game

The game is played on a rectangular grid. A typical board contains:

- A playing field
- Two goals
- A ball placed in the center
- Grid points connected by possible movement lines

The exact board size can be changed, but the basic rules stay the same.

## Basic Rules

1. The game starts with the ball in the center of the field.

2. Players take turns moving the ball.

3. A move consists of drawing a line from the current ball position to one of the neighboring grid points.

4. The ball can usually move in 8 directions:
   - Up
   - Down
   - Left
   - Right
   - Up-left
   - Up-right
   - Down-left
   - Down-right

5. A line that has already been drawn cannot be drawn again.

6. The ball cannot move outside the allowed playing area, except when entering a goal.

7. If the ball reaches the opponent's goal, the current player wins.

8. If a player has no legal move, they lose the game.

---

## Bounce Rule

One of the most important rules of paper soccer is the **bounce rule**.

If the ball moves to a point that was already visited before, or to a wall/border point, the same player gets another move.

This means that one player can sometimes make several moves in one turn. These chained moves can be very important strategically.

For example:

- If the ball moves to an empty point, the turn usually ends.
- If the ball moves to a previously visited point, the player continues.
- If the ball bounces from the border, the player continues.
- If the player reaches the goal, the game ends immediately.

This rule makes the game much more complex, because the model must not only choose a single line, but also understand possible move sequences.

---

## Winning Conditions

A player wins when they move the ball into the opponent's goal.

For example:

- Player 1 may try to score in the upper goal.
- Player 2 may try to score in the lower goal.

The game can also end if a player gets trapped and has no valid move. In that case, the player who cannot move loses.

---

## Illegal Moves

A move is illegal if:

- It uses a line that has already been drawn.
- It moves outside the board.
- It moves through an invalid position.
- It does not start from the current ball position.
- It does not end on a neighboring grid point.
- It violates the game boundary rules.

The game engine must check all moves before applying them.

---

# Project Goal

The main goal of this project is to build a neural network that can play paper soccer.

The project will not only focus on creating a playable game, but also on designing a system that can evaluate positions and make intelligent decisions.

The goals of the project are:

## 1. Implement the Paper Soccer Game

The first goal is to create a working implementation of the game.

This includes:

- Creating the board
- Defining legal moves
- Storing drawn lines
- Tracking the ball position
- Detecting goals
- Detecting blocked positions
- Handling the bounce rule
- Handling turns
- Checking game-over conditions

The game engine should be separated from the machine learning model so that it can be tested independently.

---

## 2. Represent the Game State

The second goal is to represent the paper soccer board in a form that can be used by a neural network.

A neural network cannot directly understand a visual board like a human. Therefore, we need to encode the board as numerical data.

Possible representations include:

- Matrix representation of visited points
- Matrix representation of used edges
- Current ball position
- Current player
- Available legal moves
- Goal positions
- Distance to goal
- Number of possible moves from the current position

The representation should contain enough information for the model to understand the position.

---

## 3. Create a Position Evaluation Model

Another important goal is to create a model that can evaluate a position.

The evaluation model should answer the question:

> How good is this position for the current player?

The output may be:

- A score between `-1` and `1`
- A probability of winning
- A value estimating the strength of the current position
- A ranking of possible moves

For example:

- `1.0` could mean a very good or winning position.
- `0.0` could mean a neutral position.
- `-1.0` could mean a losing position.

This is similar to how chess engines evaluate board positions.

---

## 4. Build a Move-Choosing Neural Network

The main neural network should be able to choose a move based on the current board state.

The model may work in one of two ways:

### Option 1: Policy Network

A policy network directly predicts the best move.

Input:

- Current board state

Output:

- Probabilities for all possible moves

The move with the highest probability is chosen.

### Option 2: Value Network

A value network evaluates the position after each possible move.

The algorithm checks all legal moves, applies each move temporarily, and uses the neural network to evaluate the resulting position.

The move with the best evaluation is chosen.

### Option 3: Combined Policy and Value Network

A more advanced approach is to create a model that outputs both:

- A move probability distribution
- A position value

This is similar to approaches used in modern game-playing AI systems.

---

## 5. Allow the Model to Play Against a Human

The project should allow a human player to play against the neural network.

This mode is useful because it allows us to test whether the neural network makes reasonable decisions.

The player should be able to:

- See the board
- Make a move
- Play against the model
- See the model's response
- Finish a complete game

This mode makes the project more interactive and easier to present.

---

## 6. Allow the Model to Play Against Itself

The neural network should also be able to play games against itself.

This is useful for generating training data and improving the model.

In self-play mode:

1. The model starts a new game.
2. It chooses moves for both players.
3. The game continues until someone wins or loses.
4. The final result is stored.
5. The played positions can be used as training examples.

Self-play is important because paper soccer does not have a large ready-made dataset. The model can generate its own experience by playing many games.

---

# Machine Learning Idea

The game can be treated as a reinforcement learning or supervised learning problem.

There are several possible approaches.

---

## Supervised Learning

In supervised learning, we would train the model on examples of good moves.

Each training example could contain:

- Board state
- Correct move
- Game result

The model learns to imitate good decisions.

However, this approach requires a dataset. Since paper soccer datasets are not commonly available, we may need to generate one ourselves.

Possible data sources:

- Human-played games
- Random games
- Games generated by a simple rule-based bot
- Games generated by self-play

---

## Reinforcement Learning

In reinforcement learning, the model learns by playing games.

The model receives rewards depending on the result.

Example reward system:

- `+1` for winning
- `-1` for losing
- Small positive reward for moving closer to the goal
- Small negative reward for moving into dangerous positions
- Penalty for getting trapped

The model improves by trying many games and learning which decisions lead to better results.

This approach is more complex, but it fits the project very well.

---

## Hybrid Approach

A practical solution is to start with a simpler approach and then improve it.

For example:

1. Create a random player.
2. Create a rule-based player.
3. Generate games using these players.
4. Train a neural network on the generated data.
5. Use the trained network in self-play.
6. Improve the network using results from self-play.

This approach is easier to control and debug than starting directly with advanced reinforcement learning.

---

# Game Representation

A very important part of the project is the representation of the game state.

The model needs to know:

- Where the ball is
- Which lines have already been used
- Which points have already been visited
- Where the borders are
- Where the goals are
- Which player is currently moving
- Which moves are legal

---

## Board as a Grid

The board can be represented as a grid of points.

For example:

```text
. . . . . . .
. . . . . . .
. . . O . . .
. . . . . . .
. . . . . . .
```

Where:

- `.` represents an empty point
- `O` represents the current ball position

---

## Used Edges

Since the main rule of the game is that the same line cannot be used twice, we need to store used edges.

An edge is a connection between two neighboring points.

For example, if the ball moves from `(x1, y1)` to `(x2, y2)`, then the edge between these two points becomes used.

This edge cannot be selected again later.

A good internal representation may be:

```python
used_edges = set()
```

Each edge can be stored as a pair of points:

```python
((x1, y1), (x2, y2))
```

To avoid direction problems, the edge can be normalized before storing.

For example, the edge from `A` to `B` should be the same as the edge from `B` to `A`.

---

## Neural Network Input

The neural network input could contain several layers, similar to image channels.

Example channels:

1. Current ball position
2. Visited points
3. Horizontal used edges
4. Vertical used edges
5. Diagonal used edges
6. Board boundaries
7. Goal positions
8. Current player

This would allow a convolutional neural network to process the board similarly to an image.

---

# Planned Features

The project is planned to include several important features.

---

## Basic Game Engine

The game engine should support:

- Board creation
- Player turns
- Legal move generation
- Applying moves
- Undoing moves, if needed
- Checking if the game is finished
- Detecting goals
- Detecting blocked players
- Handling repeated moves caused by bouncing

---

## Human Player Mode

In this mode, a human can play the game manually.

This is useful for:

- Testing the game rules
- Checking if the interface works
- Playing against another human
- Creating human gameplay data

---

## Neural Network Player Mode

In this mode, the model plays against a human or another model.

The neural network should:

- Receive the current board state
- Generate legal moves
- Evaluate possible moves
- Select the best move
- Apply the move

The model should never choose an illegal move. Therefore, legal move filtering is necessary.

---

## Position Evaluation

The position evaluator should estimate how strong a position is.

It may consider:

- Distance to opponent's goal
- Number of legal moves
- Risk of getting trapped
- Control over central positions
- Number of available bounce paths
- Whether the opponent is close to scoring
- Whether the current player can force a goal

This evaluation can be done manually at first and later replaced or improved by a neural network.

---

## Self-Play Mode

Self-play mode allows the model to play against itself many times.

This can be used to:

- Generate training data
- Improve the model
- Compare different model versions
- Test strategies
- Measure progress

For example, after training, we can compare:

- Random player vs trained model
- Rule-based player vs trained model
- Old model vs new model
- Model playing as first player vs second player

---

# Neural Network Player

The neural network player should make decisions based on the current board state.

A simple version of the model may use fully connected layers.

A more advanced version may use convolutional layers, because the board is grid-based.

---

## Possible Simple Model

A simple model could work like this:

1. Flatten the board representation.
2. Pass it through several fully connected layers.
3. Output scores for possible moves.

Example idea:

```text
Input board state
        |
Flatten
        |
Linear layer
        |
ReLU
        |
Linear layer
        |
ReLU
        |
Output move scores
```

This approach is easier to implement and debug.

---

## Possible CNN Model

Since the board is similar to an image, a convolutional neural network may work better.

Example idea:

```text
Input board channels
        |
Convolution
        |
ReLU
        |
Convolution
        |
ReLU
        |
Flatten
        |
Linear layer
        |
Output move scores
```

A CNN can learn local patterns, such as walls, blocked paths, and possible bounce situations.

---

## Legal Move Masking

The neural network may output scores for all possible directions.

For example, there may be 8 possible directions:

```text
0 - up
1 - down
2 - left
3 - right
4 - up-left
5 - up-right
6 - down-left
7 - down-right
```

However, not every direction is always legal.

Therefore, after the model predicts move scores, illegal moves should be removed.

Example:

```text
Raw model output:
[0.2, 0.8, 0.1, 0.4, 0.9, 0.3, 0.5, 0.7]

Legal moves:
[down, right, down-left]

After masking:
[-inf, 0.8, -inf, 0.4, -inf, -inf, 0.5, -inf]
```

The model then selects the best legal move.

This prevents the neural network from breaking the rules of the game.

---

# Self-Play

Self-play is one of the most important ideas in the project.

Because paper soccer does not have a large standard dataset, the model can learn by generating its own data.

---

## Self-Play Process

The self-play process may look like this:

1. Start a new game.
2. Let the model choose moves for both players.
3. Store every board state and selected move.
4. Continue until the game ends.
5. Assign the final result to all positions from the game.
6. Use the collected data for training.

Example:

```text
Game result: Player 1 wins

Positions where Player 1 was moving -> positive examples
Positions where Player 2 was moving -> negative examples
```

This way, the model can learn which positions usually lead to winning.

---

## Training Data From Self-Play

Each training sample may contain:

- Board state
- Current player
- Selected move
- Final game result
- Position value

Example:

```text
Input:
Current board state

Target:
Best move or final game value
```

Over many games, the model should learn to prefer moves that lead to better results.

---

# Position Evaluation

Position evaluation is a central part of the project.

The game can be evaluated using simple handcrafted rules at first.

Later, this can be replaced with a learned neural network.

---

## Simple Evaluation Ideas

A basic evaluation function may use:

- Distance from the ball to the opponent's goal
- Distance from the ball to the own goal
- Number of available legal moves
- Whether the current player has an immediate scoring move
- Whether the opponent has an immediate scoring move
- Whether the player is close to being trapped
- Whether the ball is in the center or near a dangerous border

Example evaluation:

```text
score = goal_advantage + mobility_score - danger_score
```

Where:

- `goal_advantage` rewards being closer to the opponent's goal.
- `mobility_score` rewards having many legal moves.
- `danger_score` penalizes positions where the player may get trapped.

---

## Neural Evaluation

A neural network evaluator would learn this automatically.

Instead of manually writing all rules, the model would observe many games and learn which board states are good or bad.

The output could be:

```text
value = model(board_state)
```

Where:

- A positive value means the position is good.
- A negative value means the position is bad.
- A value close to zero means the position is balanced.

---

# Possible Project Structure

A possible file structure for the project may look like this:

```text
paper-soccer-ai/
│
├── README.md
├── requirements.txt
├── main.py
│
├── game/
│   ├── board.py
│   ├── game.py
│   ├── rules.py
│   └── move.py
│
├── players/
│   ├── human_player.py
│   ├── random_player.py
│   ├── rule_based_player.py
│   └── neural_player.py
│
├── models/
│   ├── policy_network.py
│   ├── value_network.py
│   └── cnn_model.py
│
├── training/
│   ├── self_play.py
│   ├── train_policy.py
│   ├── train_value.py
│   └── dataset.py
│
├── evaluation/
│   ├── evaluate_position.py
│   ├── compare_players.py
│   └── metrics.py
│
├── ui/
│   ├── console_ui.py
│   └── visual_ui.py
│
└── saved_models/
    └── model.pth
```

---

# Technologies

The project may use the following technologies:

- Python
- NumPy
- PyTorch
- Matplotlib
- Pygame, optional
- Jupyter Notebook, optional
- Git and GitHub

---

## Python

Python will be used as the main programming language because it is simple, readable, and commonly used in machine learning.

---

## PyTorch

PyTorch will be used to create and train the neural network.

It allows us to:

- Define neural network architectures
- Train models
- Save and load models
- Use GPU acceleration if available

---

## NumPy

NumPy may be used for board representation and numerical operations.

---

## Matplotlib or Pygame

For visualization, we may use:

- Matplotlib for simple board plots
- Pygame for an interactive graphical version of the game

A console version can also be implemented first to keep the project simple.

---

# Challenges

This project has several interesting challenges.

---

## 1. Correct Rule Implementation

The rules of paper soccer must be implemented carefully.

The most important parts are:

- Detecting legal moves
- Preventing repeated edges
- Handling bounces
- Detecting goals
- Detecting trapped positions

If the game engine is incorrect, the neural network will learn from incorrect data.

---

## 2. Game State Encoding

The neural network needs a good representation of the board.

If the encoding is too simple, the model may not understand the game.

If the encoding is too complicated, training may become harder.

The representation should balance simplicity and useful information.

---

## 3. Legal Move Filtering

The model may output invalid moves.

Therefore, we need to mask illegal moves before choosing the final action.

This is important because the model should always follow the rules.

---

## 4. Lack of Dataset

There is no obvious large dataset for paper soccer.

Because of this, we need to generate training data ourselves.

Possible solutions:

- Random games
- Rule-based games
- Human-played games
- Self-play games

---

## 5. Strategic Depth

Paper soccer can contain traps and forced move sequences.

A move that looks good immediately may be bad after several turns.

Therefore, the model may need to consider future consequences.

This can be improved with:

- Self-play
- Position evaluation
- Search algorithms
- Minimax
- Monte Carlo simulations

---

# Future Improvements

After the basic project is finished, several improvements could be added.

---

## Stronger AI

The model could be improved by combining the neural network with a search algorithm.

For example:

- Minimax
- Alpha-beta pruning
- Monte Carlo Tree Search

This would allow the AI to look several moves ahead.

---

## Better Visualization

A graphical interface could make the project much easier to present.

Possible visualization features:

- Displaying the board
- Showing the current ball position
- Highlighting legal moves
- Drawing used lines
- Showing the neural network's chosen move
- Showing position evaluation score

---

## Training Dashboard

A training dashboard could show how the model improves over time.

Possible metrics:

- Win rate against random player
- Win rate against rule-based player
- Average game length
- Number of illegal move attempts before masking
- Training loss
- Position evaluation accuracy

---

## Different Board Sizes

The project could support different board sizes.

This would allow testing whether the model can generalize to new versions of the game.

---

## Human Game Recording

The program could allow humans to play games and save them.

These games could later be used as training data.

---

## Model Comparison

Different models could be compared.

For example:

- Random player
- Rule-based player
- Fully connected neural network
- CNN policy network
- CNN value network
- Self-play-trained model

The comparison could be presented in a table.

Example:

```text
Model                  Win Rate vs Random     Win Rate vs Rule-Based
Random Player          50%                    20%
Rule-Based Player      80%                    50%
Simple Neural Network  70%                    40%
CNN Model              85%                    60%
Self-Play Model        90%                    70%
```

---

# Expected Result

The expected result of the project is a working paper-soccer game with a neural network player.

The final version should be able to:

- Simulate a full game
- Validate legal moves
- Let a human play
- Let the neural network play
- Evaluate positions
- Generate training data using self-play
- Save and load trained models
- Compare different players

The project should demonstrate how machine learning can be applied to a simple board game and how an agent can improve through training and repeated gameplay.

---

# Summary

This project combines a classic paper game with machine learning.

Paper soccer is simple to understand but complex enough to be interesting for artificial intelligence. The game includes strategy, planning, traps, and positional evaluation. Because of this, it is a good choice for an Applied Machine Learning project.

The main objective is to create a system that can:

- Understand the rules of paper soccer
- Represent the game state numerically
- Evaluate board positions
- Choose legal and intelligent moves
- Play against humans
- Play against itself
- Improve through generated experience

The project can start with a simple rule-based and neural-network player, and later develop into a more advanced self-learning system.

---

# Authors

Project created for the Applied Machine Learning course.

Authors:

- Michał Pluciński
- Patryk Kuna

---

# License

This project is created for educational purposes.
