# heuristic.py
# Move scoring and board evaluation for the MCTS rollouts.

from game_state import WIN_LINES, OPPONENT, check_winner


def score_move(state, pos: int, use_trap: bool = True) -> float:
    m   = pos // 9
    l   = pos % 9
    sym = state.turn
    opp = OPPONENT[sym]
    score = 0.0

    small     = state._macro_cells(m)[:]
    small[l]  = sym

    if check_winner(small) == sym:
        score += 100

    small_opp    = state._macro_cells(m)[:]
    small_opp[l] = opp
    if check_winner(small_opp) == opp:
        score += 60

    # two-in-a-row inside the local board
    for a, b, c in WIN_LINES:
        trio = [small[a], small[b], small[c]]
        if trio.count(sym) == 2 and trio.count(None) == 1:
            score += 15

    # two-in-a-row on the global macro board
    projected_macro = state.macro[:]
    if check_winner(small) == sym:
        projected_macro[m] = sym
    for a, b, c in WIN_LINES:
        trio = [projected_macro[a], projected_macro[b], projected_macro[c]]
        if trio.count(sym) == 2 and trio.count(None) == 1:
            score += 25

    # sending the opponent into a finished macro gives them a free move anywhere. 
    # fixed the sign flip issue here. took way too long to realize it was just a +18 that needed to be a -8.
    # the +18 was literally rewarding the AI for handing the opponent a free turn.
    target = l
    if state.macro[target]:
        score -= 8

    # local center/corner preference
    if l == 4:               score += 12   
    if l in (0, 2, 6, 8):    score += 6    

    # macro center/corner preference
    if m == 4:               score += 8    
    if m in (0, 2, 6, 8):    score += 3    

    if use_trap:
        score += trap_bonus(state, pos, sym)

    return score


def _count_macro_threats(macro_9: list, sym: str) -> int:
    # counts active two-in-a-row lines on the global board
    count = 0
    for a, b, c in WIN_LINES:
        trio = [macro_9[a], macro_9[b], macro_9[c]]
        if trio.count(sym) == 2 and trio.count(None) == 1:
            count += 1
    return count


def trap_bonus(state, pos: int, sym: str) -> float:
    # evaluates if a move creates or blocks a macro fork.
    m   = pos // 9
    opp = OPPONENT[sym]

    small_after = state._macro_cells(m)[:]
    small_after[pos % 9] = sym
    macro_after = state.macro[:]
    if check_winner(small_after) == sym:
        macro_after[m] = sym

    threats_before = _count_macro_threats(state.macro, sym)
    threats_after  = _count_macro_threats(macro_after, sym)
    new_threats    = threats_after - threats_before

    opp_threats_before = _count_macro_threats(state.macro, opp)
    opp_threats_after  = _count_macro_threats(macro_after, opp)
    blocked_opp        = max(0, opp_threats_before - opp_threats_after)

    bonus = 0.0
    if threats_after >= 3:
        bonus += 40     # triple threat
    elif new_threats >= 2:
        bonus += 80     # created a fork
    elif new_threats == 1 and threats_after >= 2:
        bonus += 40     # extended an existing fork
    elif new_threats == 1:
        bonus += 20     

    if blocked_opp >= 2:
        bonus += 50     # broke opponent fork
    elif blocked_opp == 1:
        bonus += 15     

    return bonus


def board_eval(state, ai_sym: str) -> float:
    # lightweight terminal approximation for early rollout cutoff.
    opp = OPPONENT[ai_sym]
    val = 0.0

    for i, ms in enumerate(state.macro):
        if ms == ai_sym:
            val += 0.40
            if i == 4:             val += 0.10
            if i in (0,2,6,8):     val += 0.05
        elif ms == opp:
            val -= 0.40
            if i == 4:             val -= 0.10
            if i in (0,2,6,8):     val -= 0.05

    for a, b, c in WIN_LINES:
        trio = [state.macro[a], state.macro[b], state.macro[c]]
        if trio.count(ai_sym) == 2 and trio.count(None) == 1:
            val += 0.30
        if trio.count(opp) == 2 and trio.count(None) == 1:
            val -= 0.30

    val += _count_macro_threats(state.macro, ai_sym)  * 0.05
    val -= _count_macro_threats(state.macro, opp)     * 0.05

    # clamping to [-1.0, 1.0] so the math doesn't blow up downstream
    return max(-1.0, min(1.0, val))
