## ultimate-tic-tac-toe-using-heuristic-guided-monte-carlo-tree-search

A playable **Ultimate Tic-Tac-Toe** game featuring a custom space-themed web UI and an experimental **Heuristic-Guided Monte Carlo Tree Search (HG-MCTS)** agent.

This project explores the use of heuristic-guided search, transposition-table caching, and tactical pattern detection in Ultimate Tic-Tac-Toe. The AI is currently under active development and should be considered an experimental implementation rather than a strong or fully optimized engine.

![Home](home.png)

---

## Project Status

⚠️ **Work in Progress**

The current HG-MCTS agent is capable of playing complete games and demonstrates basic tactical behavior. However, its playing strength remains limited, and it frequently makes suboptimal strategic decisions.

This repository focuses on experimenting with search enhancements and evaluation techniques rather than achieving competitive-level play.

---

## What is Ultimate Tic-Tac-Toe?

Ultimate Tic-Tac-Toe is a meta-game played on a 9×9 grid divided into nine 3×3 small boards.

- Each move determines which small board the opponent must play in next.
- Winning a small board claims that position on the macro board.
- Win three claimed boards in a row on the macro board to win the game.
- If sent to a completed board, the player may choose any available board.

![Game](game.png)

---

## The AI Engine: Experimental 3-Stage HG-MCTS

Traditional MCTS often struggles in Ultimate Tic-Tac-Toe because random rollouts rarely reach meaningful terminal positions. This project explores several techniques intended to improve search quality.

| Stage | Name | Description |
| :--- | :--- | :--- |
| **Stage 1** | **HG-MCTS Base** | Uses heuristic-guided rollouts instead of purely random simulations and applies an early rollout cutoff. |
| **Stage 2** | **Transposition Table** | Uses Zobrist hashing to cache previously evaluated positions and reduce redundant search effort. |
| **Stage 3** | **Trap Detection** | Experimental fork-detection heuristics that attempt to identify macro-board threats and defensive responses. |

The effectiveness of these techniques is still being evaluated and tuned.

---
## Current Limitations

- Heuristic weights are manually tuned and remain experimental.
- The agent can miss important long-term strategic opportunities.
- Tactical pattern recognition is limited.
- Search quality varies significantly between positions.

---

## Alternative Implementation

For a stronger baseline implementation, see:

🔗 https://github.com/LucifersBossyCat/UTTT-using-minimax-and-alpha-beta-pruning

The HG-MCTS agent in this repository is still experimental and often makes poor strategic decisions. The Minimax + Alpha-Beta version currently performs more consistently and is being used as a reference point while further improvements to HG-MCTS are explored.

---

## Experimental Evaluation Heuristics

The AI evaluates non-terminal positions using a weighted heuristic system that prioritizes tactical and positional patterns such as:

- Immediate local-board wins
- Blocking opponent wins
- Macro-board progress
- Center and corner control
- Potential fork creation
- Potential fork prevention

The scoring weights are still under development and may change as the project evolves.

---

## Future Improvements

- Improved board evaluation functions
- Stronger tactical pattern recognition
- Better rollout policies
- Automated parameter tuning
- Benchmarking against alternative approaches
- Performance optimization and profiling

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/LucifersBossyCat/ultimate-tic-tac-toe-using-heuristic-guided-monte-carlo-tree-search.git
