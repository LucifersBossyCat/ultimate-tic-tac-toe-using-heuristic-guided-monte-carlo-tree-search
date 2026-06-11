"""
players.py — Human and RandomBot players
"""

import random


class Human:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def get_move(self, state, _prev_move=None) -> int:
        valid = state.valid_moves()
        print(f"  Valid moves (0-80): {valid[:10]}{'...' if len(valid) > 10 else ''}")
        while True:
            try:
                raw = input(f"  Your move [{self.symbol}] (enter 0-80): ").strip()
                pos = int(raw)
                if pos in valid:
                    return pos
                print("  ✗ Not a valid move, try again.")
            except (ValueError, EOFError):
                print("  ✗ Enter a single integer.")


class RandomBot:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def get_move(self, state, _prev_move=None) -> int:
        return random.choice(state.valid_moves())
