
import random as _random

WIN_LINES = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
OPPONENT  = {'X': 'O', 'O': 'X'}

# Zobrist tables setup
# hardcoding the seed. debugging non-deterministic tree traverses is a nightmare.
_rng = _random.Random(0xDEADBEEF)         
ZOBRIST_CELLS = [[_rng.getrandbits(64) for _ in range(2)] for _ in range(81)]
ZOBRIST_TURN  = _rng.getrandbits(64)       
SYM_IDX       = {'X': 0, 'O': 1}


def check_winner(cells_9):
    for a, b, c in WIN_LINES:
        if cells_9[a] and cells_9[a] == cells_9[b] == cells_9[c]:
            return cells_9[a]
    return None


class GameState:

    __slots__ = ('cells', 'macro', 'prev_move', 'turn', 'zobrist')

    def __init__(self):
        self.cells     = [None] * 81
        self.macro     = [None] * 9
        self.prev_move = None
        self.turn      = 'X'
        self.zobrist   = 0          

   
    def _macro_cells(self, m):
        base = m * 9
        return self.cells[base:base + 9]

    def _recompute_macro(self, m):
        c = self._macro_cells(m)
        winner = check_winner(c)
        if winner:
            self.macro[m] = winner
        elif all(c):
            self.macro[m] = 'D'

    def active_macro(self):
        # returns the sub-board index the player is forced into, or None if they can play anywhere
        if self.prev_move is None:
            return None
        target = self.prev_move % 9
        return None if self.macro[target] else target


    def valid_moves(self):
        am = self.active_macro()
        moves = []
        for m in range(9):
            if am is not None and m != am:
                continue
            if self.macro[m]:
                continue
            base = m * 9
            for l in range(9):
                if not self.cells[base + l]:
                    moves.append(base + l)
        return moves


    def play(self, pos):
        # copying arrays directly instead of deepcopying the whole object to keep node expansion fast
        g            = GameState()
        g.cells      = self.cells[:]
        g.macro      = self.macro[:]
        g.prev_move  = pos
        g.turn       = OPPONENT[self.turn]

        g.cells[pos] = self.turn
        g._recompute_macro(pos // 9)

        # incremental hash update. 
        # flipping the turn token and new cell token directly so we don't have to re-hash the whole board.
        h = self.zobrist
        if self.turn == 'O':
            h ^= ZOBRIST_TURN              
        h ^= ZOBRIST_CELLS[pos][SYM_IDX[self.turn]]
        if g.turn == 'O':
            h ^= ZOBRIST_TURN  
        g.zobrist = h

        return g


    def terminal(self):
        """Returns 'X', 'O', 'D', or None."""
        winner = check_winner(self.macro)
        if winner:
            return winner
        if all(self.macro):
            return 'D'
        return None


    def display(self):
        # CLI visualizer (mostly just for my own sanity checking during development)
        try:
            from colorama import Fore, Style, init
            init(autoreset=True)
            SYM_COLOR   = {'X': Fore.RED, 'O': Fore.CYAN, None: Fore.WHITE}
            DIV_COLOR   = Fore.GREEN
            EMPTY_COLOR = Fore.YELLOW
            reset       = Style.RESET_ALL
        except ImportError:
            SYM_COLOR = {'X': '', 'O': '', None: ''}
            DIV_COLOR = EMPTY_COLOR = reset = ''

        am = self.active_macro()
        lines = []
        for row in range(3):
            for inner_row in range(3):
                row_parts = []
                for col in range(3):
                    m  = row * 3 + col
                    ms = self.macro[m]
                    highlight = (am is None or am == m) and not ms
                    part = ''
                    for inner_col in range(3):
                        l   = inner_row * 3 + inner_col
                        pos = m * 9 + l
                        v   = self.cells[pos]
                        if v:
                            part += SYM_COLOR[v] + v + ' '
                        elif ms:
                            part += EMPTY_COLOR + '· '
                        else:
                            part += (SYM_COLOR[None] if highlight else EMPTY_COLOR) + '· '
                    row_parts.append(part)
                lines.append((DIV_COLOR + '| ').join(row_parts))
            if row < 2:
                lines.append(DIV_COLOR + '-' * 35)

        print()
        macro_display = ''
        for i, ms in enumerate(self.macro):
            macro_display += (SYM_COLOR.get(ms, '') + (ms or '·') + ' ')
            if i % 3 == 2:
                macro_display += '  '
        print(f"  Macro board: {macro_display}")
        if am is not None:
            print(f"  Must play in zone: {am // 3},{am % 3}  (macro index {am})")
        else:
            print("  Free choice — any open zone")
        print()
        for line in lines:
            print('  ' + line)
        print(reset)
