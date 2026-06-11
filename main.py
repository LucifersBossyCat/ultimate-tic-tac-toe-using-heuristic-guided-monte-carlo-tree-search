"""
main.py — Game loop for Ultimate Tic-Tac-Toe with HG-MCTS

Encoding
────────
The 9×9 board is a flat integer 0..80.
  macro index  m = pos // 9   (which small board, row-major 0-8)
  local index  l = pos  % 9   (which cell inside that small board)

Stage flags exposed at game setup
──────────────────────────────────
  Stage 1 (HG-MCTS)    — always on
  Stage 2 (TT)         — toggled per AI player
  Stage 3 (Trap)       — toggled per AI player
"""

import math
from game_state import GameState, OPPONENT
from hg_mcts   import HGMCTS, TranspositionTable
from players   import Human, RandomBot

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
    RED, CYAN, GREEN, RESET = Fore.RED, Fore.CYAN, Fore.GREEN, Style.RESET_ALL
except ImportError:
    RED = CYAN = GREEN = RESET = ''


def pick_player(symbol: str, shared_tt: TranspositionTable):
    print(f"\n  Choose player {symbol}:")
    print("    1. Human")
    print("    2. HG-MCTS AI  (time-based, default 1 s/move)")
    print("    3. HG-MCTS AI  (iteration-based)")
    print("    4. Random bot")
    choice = input("  > ").strip()

    if choice == '1':
        return Human(symbol)

    if choice in ('2', '3'):
        # Stage controls
        print("\n  Stage 2 — Transposition table? [Y/n]: ", end='')
        use_tt   = input().strip().lower() != 'n'
        print("  Stage 3 — Trap detection?        [Y/n]: ", end='')
        use_trap = input().strip().lower() != 'n'

        tt = shared_tt if use_tt else None

        if choice == '2':
            raw = input("  Seconds per move [1.0]: ").strip()
            t   = float(raw) if raw else 1.0
            return HGMCTS(symbol, time_limit=t,
                          use_tt=use_tt, tt=tt, use_trap=use_trap)
        else:
            raw = input("  Iterations per move [1500]: ").strip()
            n   = int(raw) if raw else 1500
            return HGMCTS(symbol, iterations=n,
                          use_tt=use_tt, tt=tt, use_trap=use_trap)

    return RandomBot(symbol)


def print_banner():
    print(RED + "\n  ╔═══════════════════════════════════════════════════╗")
    print(RED + "  ║   Ultimate Tic-Tac-Toe  ·  HG-MCTS  Stage 1-2-3  ║")
    print(RED + "  ╚═══════════════════════════════════════════════════╝" + RESET)
    print(CYAN + """
  Stages
  ──────
  Stage 1  HG-MCTS        heuristic-guided rollouts + early cutoff
  Stage 2  Trans. Table   reuse stats across transpositions & turns
  Stage 3  Trap detect.   fork-aware scoring on macro board

  Encoding: cells are numbered 0-80  (macro = pos//9, local = pos%9)
  """ + RESET)


def main():
    print_banner()

    # Shared transposition table — both AI players can contribute to it
    shared_tt = TranspositionTable()

    p1 = pick_player('X', shared_tt)
    p2 = pick_player('O', shared_tt)
    players = {'X': p1, 'O': p2}

    wins = {'X': 0, 'O': 0, 'D': 0}

    while True:
        state = GameState()
        state.display()

        while True:
            player = players[state.turn]
            sym    = state.turn
            color  = RED if sym == 'X' else CYAN
            kind   = 'Human' if isinstance(player, Human) \
                     else ('AI' if isinstance(player, HGMCTS) else 'Random')

            print(f"\n  {GREEN}{'─'*48}{RESET}")
            print(f"  Turn: {color}{sym}{RESET}  ({kind})")

            move  = player.get_move(state)
            state = state.play(move)
            print(f"  Played position {move}  (macro {move//9}, local {move%9})")
            state.display()

            result = state.terminal()
            if result:
                wins[result] += 1
                if result == 'D':
                    print(f"\n  {GREEN}Draw!{RESET}")
                else:
                    c = RED if result == 'X' else CYAN
                    print(f"\n  {c}{result} wins!{RESET}")
                print(f"  Score — X: {wins['X']}  O: {wins['O']}  Draws: {wins['D']}")
                break

        again = input("\n  Play again? [Y/n]: ").strip().lower()
        if again == 'n':
            break

    print(f"\n  Final — X: {wins['X']}  O: {wins['O']}  Draws: {wins['D']}")
    print("  Thanks for playing!\n")


if __name__ == '__main__':
    main()
