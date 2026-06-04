# Paper Soccer AI

## Project Description

Paper Soccer AI is a project created for the **Applied Machine Learning** course.
The goal of the project is to implement the classic **Paper Soccer** game and test several computer players, including a simple neural-network player trained with **PyTorch**.

The project is split into two main parts:

```text
C++    -> game engine, rules, legal moves and gameplay loop
Python -> bots, search algorithm, dataset generation, training and web visualization
```

Paper Soccer is a two-player strategy game played on a rectangular grid. Players move the ball by drawing lines between neighboring points. A used line cannot be used again. The objective is to reach the opponent's goal or force the opponent into a position with no legal moves.

Even though the rules are simple, the game can quickly become strategic. Each move changes the board, blocks one edge and may create an extra move because of the bounce rule. This makes the game a nice small environment for testing search algorithms and neural networks.

---

## Game Rules

The game is played on a grid with two goals. In this project the board size is:

```text
Width: 11 vertices
Height: 13 vertices
Goal width: 5 vertices
```

### Basic Rules

1. The ball starts in the middle of the board.
2. Players take turns moving the ball.
3. A move is made to one of 8 neighboring points.
4. A line that was already used cannot be used again.
5. The ball cannot leave the field, except when it enters a goal.
6. A player wins by moving the ball into the opponent's goal.
7. If a player has no legal moves, that player loses.

### Bounce Rule

If the ball reaches a point that was already visited, or reaches the border of the field, the same player moves again.

Because of this, one turn may contain more than one small move. This is one of the reasons why Paper Soccer is more interesting than it looks at first.

---

## Move Controls

In the terminal version, moves are selected using numpad-style controls:

```text
7 8 9
4   6
1 2 3
```

They correspond to directions around the current ball position:

```text
8 -> up
9 -> up-right
6 -> right
3 -> down-right
2 -> down
1 -> down-left
4 -> left
7 -> up-left
```

In the web version, legal moves are shown as green clickable circles.

---

## Implemented Modes

When the game starts, the player can choose the bot mode:

```text
1 - heuristic
2 - search
3 - neural
```

### Heuristic Mode

The heuristic bot uses a hand-written evaluation of the current position. It checks legal moves and scores them using simple game features, for example progress toward the goal and mobility.

This mode is simple, fast and useful as a baseline.

### Search Mode

The search bot uses a minimax-like **negamax** search with alpha-beta pruning. It simulates future moves and tries to find the move that gives the best result for the current player.

This is usually the strongest implemented mode because it actually looks ahead.

### Neural Mode

The neural bot uses a PyTorch model. The current board state is converted into one vector and passed to a fully connected neural network. The network outputs 8 scores, one for each possible direction.

Illegal moves are masked before choosing the final move, so the neural bot should only play legal moves.

---

## Machine Learning Approach

The model treats Paper Soccer as a move prediction problem.

```text
board state -> neural network -> move scores
```

The network output has 8 values:

```text
0 - up
1 - up-right
2 - right
3 - down-right
4 - down
5 - down-left
6 - left
7 - up-left
```

The board state contains:

- current player
- current ball position
- allowed directions from every vertex
- visited / extra-turn vertices

The model does not directly control the game rules. The C++ engine and Python logic still check legal moves.

---

## Project Structure

```text
paper-soccer-ai/
├── cpp/
│   ├── include/
│   │   ├── direction.hpp
│   │   ├── field.hpp
│   │   ├── game.hpp
│   │   └── types.hpp
│   ├── src/
│   │   ├── field.cpp
│   │   ├── game.cpp
│   │   └── main.cpp
│   └── CMakeLists.txt
│
├── python/
│   ├── dataset.py
│   ├── evaluation.py
│   ├── generate_dataset.py
│   ├── model.py
│   ├── parse.py
│   ├── play.py
│   ├── search_bot.py
│   ├── train.py
│   ├── visualize_game.py
│   └── web_server.py
│
├── README.md
└── instruction.txt
```

---

## What Each Part Does

### C++ Files

`direction.hpp` defines the 8 possible move directions, direction masks and opposite directions.

`types.hpp` stores shared type aliases used by the field and game logic.

`field.hpp` and `field.cpp` build the board. They calculate vertices, borders, goals, neighbors and initially allowed directions.

`game.hpp` and `game.cpp` contain the main game rules. They store the current player, ball position, used edges, visited points, winner detection, dead-end detection and saving the game state to `gamestate.txt`.

`main.cpp` is the main game program. It lets the user choose a side, choose a bot mode, play in the terminal or run the web mode. It also calls the Python bot when the AI has to move.

`CMakeLists.txt` is used to build the C++ executable with CMake.

### Python Files

`parse.py` loads `cpp/gamestate.txt` and converts it into a Python `GameState` object. It also creates the tensor input used by the neural network.

`evaluation.py` contains the heuristic evaluation functions. It scores positions and moves using simple game logic.

`search_bot.py` contains the search-based bot. It clones game states, applies moves, checks terminal positions and uses negamax with alpha-beta pruning.

`play.py` is called by the C++ program when the bot needs to move. It reads the current game state, chooses a move using heuristic, search or neural mode, and saves the chosen move into `move.txt`.

`model.py` defines the neural network architecture and the function for choosing the best legal neural move.

`generate_dataset.py` generates training samples by simulating games and using the search bot as an expert. It saves tensors such as states, targets, legal masks and best moves.

`train.py` trains the neural network on the generated dataset. It splits the data into training and test parts, trains the model, evaluates it and saves the best model.

`dataset.py` defines a small PyTorch dataset wrapper.

`visualize_game.py` creates a static `board.html` visualization from the current game state.

`web_server.py` starts a local web server. It shows the board in the browser, refreshes the game state and lets the human player choose legal moves by clicking.

---

## Training Explanation

The training pipeline uses tensors saved by `generate_dataset.py`:

```text
states.pt       -> board states
 targets.pt      -> target move scores
legal_masks.pt  -> which moves are legal
best_moves.pt   -> best move index for each state
```

In `train.py`, these tensors are combined into one dataset:

```python
dataset = TensorDataset(states, targets, legal_masks, best_moves)
```

Then the dataset is split into training and testing data:

```python
train_size = int(0.8 * len(dataset))
test_size = len(dataset) - train_size
```

This means:

- `80%` of all samples are used for training
- `20%` of all samples are used for testing

For example, if the dataset has `10000` samples:

```text
train_size = 8000
test_size = 2000
```

The test set is not used for learning. It is used only to check if the model works well on positions it did not train on.

The model is saved when the test top-3 accuracy improves:

```text
python/saved_models/policy_model_v2.pth
```

The training history is saved to:

```text
python/saved_models/training_history_v2.csv
```

---

## Important Dataset Note

The heavy dataset files are not included in the repository. They can be generated again when needed.

At the moment, `generate_dataset.py` saves data into:

```text
python/data/
```

and `train.py` expects data in:

```text
python/data/
```

---

## How to Run

### 1. Create Python Environment

From the project root:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install needed packages:

```bash
pip install torch
```

### 2. Build the C++ Game

Go to the `cpp` folder:

```bash
cd cpp
```

Configure and build:

```bash
cmake -S . -B build
cmake --build build
```

The executable should be created in:

```text
cpp/build/soccer.exe
```

### 3. Run the Terminal Game

From the `cpp` folder:

```bash
./build/soccer.exe
```

Then choose:

```text
0 - Top
1 - Bottom
```

and choose a bot:

```text
1 - heuristic
2 - search
3 - neural
```

Use the numpad-style controls to make moves.

### 4. Run the Web Version

Open two terminals.

In the first terminal, start the Python web server from the project root:

```bash
python python/web_server.py
```

Then open:

```text
http://localhost:5000
```

In the second terminal, go to the C++ folder and run:

```bash
cd cpp
./build/soccer.exe web
```

The board will be shown in the browser. When it is your turn, click one of the green legal move circles.

---

## How to Generate Data and Train the Neural Bot

First make sure the C++ game created an initial `gamestate.txt`. You can run:

```bash
cd cpp
./build/soccer.exe init
```

Then generate the dataset:

```bash
cd ..
python python/generate_dataset.py
```

After that, make sure `train.py` reads from the same folder where the dataset was saved. Then run:

```bash
python python/train.py
```

After training, the model should be saved in:

```text
python/saved_models/policy_model_v2.pth
```

Then neural mode can load this model and use it during the game.

---

## Notes

The repository does not include large generated dataset files, because they are heavy and can be recreated.

The project currently contains three levels of AI:

```text
heuristic -> simple hand-written logic
search    -> stronger look-ahead bot
neural    -> PyTorch policy model trained from generated examples
```

The main idea is to connect a clean C++ game engine with Python machine-learning tools and make the game playable both from the terminal and from a small local web interface.

## Authors

Project created for the Applied Machine Learning course at AGH.

Authors:

- Michał Pluciński
- Patryk Kuna

---