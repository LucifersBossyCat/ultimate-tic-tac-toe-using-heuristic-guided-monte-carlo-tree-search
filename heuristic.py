"""
heuristic.py — Move scoring and board evaluation for HG-MCTS

"""

from game_state import WIN_LINES, OPPONENT, check_winner


# Stage 1: base move scoring 

def score_move(state, pos: int, use_trap: bool = True) -> float:
    m   = pos // 9
    l   = pos % 9
    sym = state.turn
    opp = OPPONENT[sym]
    score = 0.0

    small     = state._macro_cells(m)[:]
    small[l]  = sym

    # 1. Immediate small-board win
    if check_winner(small) == sym:
        score += 100

    # 2. Block opponent small-board win
    small_opp    = state._macro_cells(m)[:]
    small_opp[l] = opp
    if check_winner(small_opp) == opp:
        score += 60

    # 3. Two-in-a-row inside the small board
    for a, b, c in WIN_LINES:
        trio = [small[a], small[b], small[c]]
        if trio.count(sym) == 2 and trio.count(None) == 1:
            score += 15

    # 4. Two-in-a-row on the macro board
    projected_macro = state.macro[:]
    if check_winner(small) == sym:
        projected_macro[m] = sym
    for a, b, c in WIN_LINES:
        trio = [projected_macro[a], projected_macro[b], projected_macro[c]]
        if trio.count(sym) == 2 and trio.count(None) == 1:
            score += 25

    # 5. Send opponent into a finished macro (they are forced to play freely,
    #    which is only a minor advantage — we reward the constraint itself)
    target = l
    if state.macro[target]:
        score += 18

    # 6. Positional bonuses (local)
    if l == 4:               score += 12   # center cell
    if l in (0, 2, 6, 8):   score += 6    # corner cell

    # 7. Macro-level positional bonus
    if m == 4:               score += 8    # center macro
    if m in (0, 2, 6, 8):   score += 3    # corner macro

    # 8. Stage 3 — trap detection
    if use_trap:
        score += trap_bonus(state, pos, sym)

    return score


# Stage 3: trap detection
#
# Weights
# ───────
#   +80  creating a fork (two macro threats)
#   +50  blocking opponent fork
#   +40  creating a triple threat (≥3 lines threatened)

def _count_macro_threats(macro_9: list, sym: str) -> int:
    """Count lines that are (sym, sym, None) in any order."""
    opp   = OPPONENT[sym]
    count = 0
    for a, b, c in WIN_LINES:
        trio = [macro_9[a], macro_9[b], macro_9[c]]
        if trio.count(sym) == 2 and trio.count(None) == 1:
            count += 1
    return count


def trap_bonus(state, pos: int, sym: str) -> float:
    """
    Return an additional score for moves that create or destroy macro forks.
    Called by score_move(); can also be called standalone.
    """
    m   = pos // 9
    opp = OPPONENT[sym]

    # Project macro state after this move
    small_after = state._macro_cells(m)[:]
    small_after[pos % 9] = sym
    macro_after = state.macro[:]
    if check_winner(small_after) == sym:
        macro_after[m] = sym

    # Count threats before and after for both players
    threats_before = _count_macro_threats(state.macro, sym)
    threats_after  = _count_macro_threats(macro_after, sym)
    new_threats    = threats_after - threats_before

    opp_threats_before = _count_macro_threats(state.macro, opp)
    # Simulate what the opponent would have had without this blocking move
    # (we only block if we win macro m, removing it from their attack surface)
    opp_threats_after  = _count_macro_threats(macro_after, opp)
    blocked_opp        = max(0, opp_threats_before - opp_threats_after)

    bonus = 0.0
    if threats_after >= 3:
        bonus += 40     # triple threat — very strong position
    elif new_threats >= 2:
        bonus += 80     # created a fork
    elif new_threats == 1 and threats_after >= 2:
        bonus += 40     # extended an existing fork
    elif new_threats == 1:
        bonus += 20     # opened one new line

    if blocked_opp >= 2:
        bonus += 50     # broke opponent fork
    elif blocked_opp == 1:
        bonus += 15     # closed one opponent threat

    return bonus


# Board evaluation (used for early rollout cutoff) 

def board_eval(state, ai_sym: str) -> float:
    """
    Lightweight terminal-approximation.  Returns a value in [-1, +1].
    Incorporates macro ownership, two-in-a-row patterns, and trap count.
    """
    opp = OPPONENT[ai_sym]
    val = 0.0

    for i, ms in enumerate(state.macro):
        if ms == ai_sym:
            val += 0.40
            if i == 4:             val += 0.10
            if i in (0,2,6,8):    val += 0.05
        elif ms == opp:
            val -= 0.40
            if i == 4:             val -= 0.10
            if i in (0,2,6,8):    val -= 0.05

    for a, b, c in WIN_LINES:
        trio = [state.macro[a], state.macro[b], state.macro[c]]
        if trio.count(ai_sym) == 2 and trio.count(None) == 1:
            val += 0.30
        if trio.count(opp) == 2 and trio.count(None) == 1:
            val -= 0.30

    # Trap component (normalised — each fork worth ~0.15)
    val += _count_macro_threats(state.macro, ai_sym)  * 0.05
    val -= _count_macro_threats(state.macro, opp)     * 0.05

    return max(-1.0, min(1.0, val))
