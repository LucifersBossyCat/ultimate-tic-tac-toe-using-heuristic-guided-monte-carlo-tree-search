# players.py
# basic human CLI input and a random bot to use as a baseline punching bag for the MCTS engine.

import random


class Human:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def get_move(self, state, _prev_move=None) -> int:
        valid = state.valid_moves()
        
        # clipping the valid moves list so the console doesn't get spammed during the early game
        print(f"  Valid moves (0-80): {valid[:10]}{'...' if len(valid) > 10 else ''}")
        
        while True:
            try:
                raw = input(f"  Your move [{self.symbol}] (enter 0-80): ").strip()
                pos = int(raw)
                if pos in valid:
                    return pos
                print("  ✗ Invalid move. Check the macro board rules.")
            except (ValueError, EOFError):
                print("  ✗ Just type an integer.")


class RandomBot:
    # literally just picks a valid move at random. 
    # used to sanity-check that the MCTS is actually doing something intelligent.
    def __init__(self, symbol: str):
        self.symbol = symbol

    def get_move(self, state, _prev_move=None) -> int:
        return random.choice(state.valid_moves())
