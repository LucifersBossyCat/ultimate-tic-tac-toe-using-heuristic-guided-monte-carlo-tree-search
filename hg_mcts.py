# hg_mcts.py
# The core MCTS engine with heuristic rollout logic and cache management.

import math
import random
import time

from game_state import GameState, OPPONENT
from heuristic  import score_move, board_eval


# TT settings
TT_MAX_SIZE  = 200_000
_PROBE_WINDOW = 16  

class TTEntry:
    __slots__ = ('visits', 'wins', 'depth')
    def __init__(self, visits=0, wins=0.0, depth=999):
        self.visits = visits
        self.wins   = wins
        self.depth  = depth

class TranspositionTable:
    # dict mapping zobrist hashes to node stats.
    # doing a lazy random-probe eviction here when the table fills up 
    # because maintaining a strict LRU queue was tanking the simulation speed.

    def __init__(self, max_size: int = TT_MAX_SIZE):
        self._table    = {}
        self._max_size = max_size
        self.hits      = 0
        self.stores    = 0
        self.evictions = 0

    def lookup(self, key: int):
        entry = self._table.get(key)
        if entry:
            self.hits += 1
        return entry

    def store(self, key: int, visits: int, wins: float, depth: int):
        if key in self._table:
            e = self._table[key]
            e.visits += visits
            e.wins   += wins
            e.depth   = min(e.depth, depth)
            return

        if len(self._table) >= self._max_size:
            self._evict()
        self._table[key] = TTEntry(visits, wins, depth)
        self.stores += 1

    def _evict(self):
        # sample a few random keys and drop the one with the lowest visit count
        keys = random.sample(list(self._table.keys()),
                             min(_PROBE_WINDOW, len(self._table)))
        victim = min(keys, key=lambda k: self._table[k].visits)
        del self._table[victim]
        self.evictions += 1

    def stats(self) -> str:
        return (f"TT size={len(self._table)}  hits={self.hits}  "
                f"stores={self.stores}  evictions={self.evictions}")

    def reset_counters(self):
        self.hits = self.stores = self.evictions = 0


class Node:
    __slots__ = ('state', 'parent', 'move', 'wins', 'visits',
                 'children', '_expanded', 'depth')

    def __init__(self, state: GameState, parent=None, move=None, depth: int = 0):
        self.state     = state
        self.parent    = parent
        self.move      = move
        self.depth     = depth
        self.wins      = 0.0
        self.visits    = 0
        self.children  = []
        self._expanded = False

    def uct(self, C: float) -> float:
        if self.visits == 0:
            return float('inf')
        parent_visits = self.parent.visits if self.parent else self.visits
        if parent_visits <= 0:
            return self.wins / self.visits
            
        exploit = self.wins / self.visits
        explore = C * math.sqrt(math.log(parent_visits) / self.visits)
        return exploit + explore

    def select(self, C: float) -> 'Node':
        if not self._expanded or not self.children:
            return self
        best = max(self.children, key=lambda n: n.uct(C))
        return best.select(C)

    def expand(self, tt: 'TranspositionTable | None' = None):
        if self.state.terminal():
            return
        moves = self.state.valid_moves()
        if not moves:
            return
            
        # sort by heuristic first so the tree explores the most promising branches immediately
        moves.sort(key=lambda m: score_move(self.state, m, use_trap=True), reverse=True)
        
        for m in moves:
            child_state = self.state.play(m)
            child       = Node(child_state, parent=self, move=m, depth=self.depth + 1)
            
            # pull stats from the transposition table if we've seen this board state in another branch
            if tt is not None:
                entry = tt.lookup(child_state.zobrist)
                if entry:
                    child.visits = entry.visits
                    child.wins   = entry.wins
            self.children.append(child)
            
        self._expanded = True

    def backprop(self, value: float, tt: 'TranspositionTable | None' = None):
        self.visits += 1
        self.wins   += value
        
        if tt is not None:
            tt.store(self.state.zobrist, 1, value, self.depth)
            
        if self.parent:
            # negamax style logic — flip the value perspective for the parent node
            self.parent.backprop(-value, tt)   


class HGMCTS:
    def __init__(self,
                 symbol:            str,
                 time_limit:        float = 1.0,
                 iterations:        int   = None,
                 C:                 float = math.sqrt(2),
                 p_greedy:          float = 0.80,
                 max_rollout_depth: int   = 35,
                 use_tt:            bool  = True,
                 tt:                'TranspositionTable | None' = None,
                 use_trap:          bool  = True,
                 verbose:           bool  = True):

        self.symbol            = symbol
        self.time_limit        = time_limit
        self.iterations        = iterations
        self.C                 = C
        self.p_greedy          = p_greedy
        self.max_rollout_depth = max_rollout_depth
        self.use_tt            = use_tt
        self.use_trap          = use_trap
        self.verbose           = verbose

        if use_tt:
            self.tt = tt if tt is not None else TranspositionTable()
        else:
            self.tt = None

    def _rollout(self, state: GameState, depth: int = 0) -> float:
        t = state.terminal()
        if t:
            if t == self.symbol: return  1.0
            if t == 'D':         return  0.0
            return -1.0

        # MCTS trees on ultimate tic-tac-toe get insanely deep. 
        # cutting it off here and relying on the static evaluator to guess the winner.
        if depth >= self.max_rollout_depth:
            return board_eval(state, self.symbol)  

        moves = state.valid_moves()
        if not moves:
            return 0.0

        # injecting some noise so it doesn't play the exact same deterministic game every time
        if random.random() < self.p_greedy:
            scored = sorted(moves,
                            key=lambda m: score_move(state, m, use_trap=self.use_trap),
                            reverse=True)
            top    = scored[:min(3, len(scored))]
            chosen = random.choice(top)
        else:
            chosen = random.choice(moves)

        return self._rollout(state.play(chosen), depth + 1)


    def get_move(self, state: GameState) -> int:
        tt = self.tt
        if tt:
            tt.reset_counters()

        root = Node(state)
        root.expand(tt)

        use_time = self.iterations is None
        deadline = time.time() + self.time_limit if use_time else None

        i = 0
        while True:
            if use_time:
                if time.time() >= deadline:
                    break
            else:
                if i >= self.iterations:
                    break
            i += 1

            node = root.select(self.C)

            if node.visits > 0 and not node._expanded:
                node.expand(tt)
                if node.children:
                    unvisited = [c for c in node.children if c.visits == 0]
                    node = unvisited[0] if unvisited else node.children[0]

            result = self._rollout(node.state)
            node.backprop(result, tt)

        if not root.children:
            return state.valid_moves()[0]

        # pick the child the search spent the most time on (most robust indicator)
        best = max(root.children, key=lambda n: n.visits)

        if self.verbose:
            top3 = sorted(root.children, key=lambda n: n.visits, reverse=True)[:3]
            tag  = "[HG-MCTS"
            if self.use_tt:   tag += "+TT"
            if self.use_trap: tag += "+Trap"
            tag += "]"
            moves_str = ", ".join(
                f"{n.move}({n.visits}v, {n.wins/n.visits:+.2f}w)" for n in top3
            )
            print(f"  {tag} {i} iters | top: {moves_str}")
            if tt:
                print(f"  {tt.stats()}")

        return best.move
