# Paper Soccer AI

## Project Description

Paper Soccer AI is a project created for the **Applied Machine Learning** course.
The goal of the project is to implement the classic **Paper Soccer** game and build a neural-network player using **PyTorch**.

The game engine will be written in **C++**, because the rules, move generation, and game simulation should be fast and clearly separated from the machine-learning code.
The neural network, training pipeline, and experiments will be written in **Python** using **PyTorch**.

Paper Soccer, also known as Paper Hockey, is a two-player strategy game played on a rectangular grid. Players move the ball by drawing lines between neighboring grid points. The objective is to reach the opponent's goal while avoiding blocked paths and losing positions.

Even though the rules are simple, the game contains many strategic decisions. Every drawn line changes the future state of the board, blocks one possible path, and may create bounce moves. This makes Paper Soccer a good small environment for machine learning.

---

## Game Rules

More information about the game rules can be found here:

https://en.wikipedia.org/wiki/Paper_soccer

The game is played on a rectangular grid representing a football field.

In our project, we plan to use a fixed board size:

```text
Width: 9 grid points
Height: 13 grid points
```

The exact size may still be adjusted during development, but using a fixed board size makes the first version easier to implement, test, and convert into tensors for the neural network.

### Basic Rules

1. The ball starts in the center of the board.
2. Players take turns moving the ball.
3. A move is made by drawing a line from the current ball position to one neighboring grid point.
4. The ball can move in 8 directions:
   - up
   - down
   - left
   - right
   - up-left
   - up-right
   - down-left
   - down-right
5. A line that has already been used cannot be used again.
6. The ball cannot leave the field, except when it enters a goal.
7. A player wins by moving the ball into the opponent's goal.
8. If a player has no legal moves, that player loses.

### Bounce Rule

If the ball reaches a point that was already visited, or touches the border of the field, the same player moves again.

This means that one turn may contain multiple small moves.  
Because of that, the model should not only understand single moves, but also positions that may lead to longer bounce sequences.

---

## Project Goals

The main goal is to create a working Paper Soccer environment and train a simple PyTorch model to play the game.

The project focuses on:

- implementing the Paper Soccer game logic in C++
- generating legal moves for the current position
- storing already used edges
- detecting goals and losing positions
- creating a clean interface between C++ and Python
- representing the board state as a tensor
- building a PyTorch neural network
- training the model on generated game data
- allowing a human to play against the model
- allowing the model to play games against itself

---

## Machine Learning Approach

The project will follow a workflow similar to basic PyTorch classification tasks.

Instead of classifying images, the model will classify possible moves.

```text
MNIST task:
image -> neural network -> digit class

Paper Soccer task:
board state -> neural network -> move direction
```

The neural network will output 8 values, one for each possible direction.

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

The move with the highest score will be selected only after checking if it is legal.

---

## Game Engine

The C++ game engine will be responsible for the actual rules of the game.

It should handle:

- board creation
- current ball position
- current player
- legal move generation
- move execution
- used edge storage
- visited point storage
- bounce detection
- goal detection
- game-over detection

The machine-learning code should not decide whether a move is legal.  
The C++ engine should always validate the move before it is applied.

This separation makes the project cleaner:

```text
C++:
game rules, legal moves, simulation

Python / PyTorch:
training, neural network, experiments
```

---

## Board Representation

Before the board is passed to the neural network, it must be converted into a tensor.

For the planned board size, a possible tensor shape is:

```text
[channels, 13, 9]
```

Example channels:

1. current ball position
2. visited points
3. board borders
4. current player

This representation is similar to an image with multiple channels, which makes it suitable for PyTorch models.

---

## Legal Move Masking

The neural network may output a high score for an illegal move.  
Because of that, illegal moves must be removed before choosing the final action.

The process is:

1. the C++ engine returns legal moves
2. the PyTorch model predicts scores for all 8 directions
3. illegal moves are masked
4. the best legal move is selected
5. the selected move is sent back to the C++ game engine

This keeps the neural-network player inside the rules of the game.

---

## Planned Modes

The project will include several modes.

### Human vs Human

Two players can play the game manually.

### Human vs Neural Network

A human player can play against the PyTorch model.

### Neural Network vs Neural Network

Two model-controlled players can play against each other.

### Self-Play

The model can generate games by playing against itself.  
These games can later be used as training data.

---

## Model

The first model will be a simple fully connected neural network.

Input:

```text
board tensor
```

Output:

```text
8 move scores
```

Example architecture:

```text
Flatten
Linear
ReLU
Linear
ReLU
Linear
Output scores
```

This model is intentionally simple, because the first goal is to build a clear and working machine-learning pipeline.

A convolutional neural network may be added later, because the board has a grid structure.

---

## Training

At the beginning, the model can be trained using games generated by simple players.

Possible data sources:

- random player games
- rule-based player games
- self-play games
- human-played games

Each training example contains:

```text
board state -> selected move
```

The model can be trained using standard PyTorch tools:

- `torch`
- `torch.nn`
- `Dataset`
- `DataLoader`
- `CrossEntropyLoss`
- `Adam`

This makes the training process similar to the PyTorch exercises from class.

---

## Suggested Project Structure

```text
paper-soccer-ai/
│
├── README.md
├── main.py
│
├── cpp/
│   ├── game.cpp
│   ├── game.hpp
│   ├── board.cpp
│   ├── board.hpp
│   └── bindings.cpp
│
├── python/
│   ├── model.py
│   ├── train.py
│   ├── play.py
│   ├── dataset.py
│   └── evaluate.py
│
└── saved_models/
    └── model.pth
```

### `cpp/game.cpp` and `cpp/game.hpp`

Contain the main game logic.

### `cpp/board.cpp` and `cpp/board.hpp`

Contain the board representation, used edges, visited points, and move validation.

### `cpp/bindings.cpp`

Contains the communication layer between C++ and Python.

### `python/model.py`

Contains the PyTorch model.

### `python/train.py`

Contains the training loop.

### `python/play.py`

Allows playing against the model.

### `python/evaluate.py`

Compares different players and model versions.

---

## Technologies

The project will use:

- C++
- Python
- PyTorch
- NumPy
- Matplotlib, optional
- Git

C++ will be used for the game engine.  
Python and PyTorch will be used for the machine-learning part.

---

## Expected Result

The expected result is a working Paper Soccer game with a basic neural-network player.

The final version should be able to:

- simulate a complete game
- check legal and illegal moves
- convert the board into a tensor
- run a forward pass through a PyTorch model
- train the model on generated data
- allow a human to play against the model
- allow model-vs-model games
- save and load trained models

---

## Future Improvements

Possible future improvements:

- better board visualization
- simple graphical interface
- convolutional neural network model
- stronger rule-based opponent
- improved self-play training
- position evaluation score
- model comparison statistics

---

## Authors

Project created for the Applied Machine Learning course.

Authors:

- Michał Pluciński
- Patryk Kuna

---

## License

This project is created for educational purposes.
