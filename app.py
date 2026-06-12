# app.py
# Flask routing and session handling for the UTTT engine.

import json
import threading
from flask import Flask, jsonify, request, render_template, session
from game_state import GameState
from hg_mcts import HGMCTS, TranspositionTable

app = Flask(__name__)
app.secret_key = 'uttt-hgmcts-secret'

# mapping session IDs to game instances. 
# using a global dict + lock here instead of a DB just to keep the setup light.
games = {}
games_lock = threading.Lock()

def get_game(sid):
    with games_lock:
        return games.get(sid)

def set_game(sid, data):
    with games_lock:
        games[sid] = data

def state_to_dict(state):
    result = state.terminal()
    return {
        'cells': state.cells,
        'macro': state.macro,
        'turn': state.turn,
        'prev_move': state.prev_move,
        'active_macro': state.active_macro(),
        'valid_moves': state.valid_moves(),
        'terminal': result,
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new_game', methods=['POST'])
def new_game():
    data = request.json or {}
    human_sym   = data.get('human_symbol', 'X')
    time_limit  = float(data.get('time_limit', 1.0))
    use_tt      = data.get('use_tt', True)
    use_trap    = data.get('use_trap', True)

    ai_sym = 'O' if human_sym == 'X' else 'X'
    tt     = TranspositionTable() if use_tt else None
    ai     = HGMCTS(
        symbol=ai_sym,
        time_limit=time_limit,
        use_tt=use_tt,
        tt=tt,
        use_trap=use_trap,
        verbose=False,
    )

    state   = GameState()
    game_id = request.remote_addr + str(id(state))

    set_game(game_id, {
        'state':      state,
        'ai':         ai,
        'human_sym':  human_sym,
        'ai_sym':     ai_sym,
        'history':    [],
    })

    response = {'game_id': game_id, 'state': state_to_dict(state), 'human_sym': human_sym}

    # if AI goes first, generate its move before returning the initial board
    if human_sym == 'O':
        ai_move  = ai.get_move(state)
        state    = state.play(ai_move)
        game     = get_game(game_id)
        game['state']    = state
        game['history'].append(ai_move)
        response['ai_move']  = ai_move
        response['state']    = state_to_dict(state)

    return jsonify(response)

@app.route('/api/move', methods=['POST'])
def make_move():
    data    = request.json or {}
    game_id = data.get('game_id')
    pos     = int(data.get('pos', -1))

    game = get_game(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    state = game['state']
    if pos not in state.valid_moves():
        return jsonify({'error': 'Invalid move'}), 400

    state = state.play(pos)
    game['history'].append(pos)
    game['state'] = state

    response = {
        'human_move': pos,
        'state':      state_to_dict(state),
        'ai_move':    None,
    }

    if not state.terminal():
        ai      = game['ai']
        ai_move = ai.get_move(state)
        state   = state.play(ai_move)
        game['history'].append(ai_move)
        game['state']      = state
        response['ai_move']  = ai_move
        response['state']    = state_to_dict(state)

    return jsonify(response)

@app.route('/api/undo', methods=['POST'])
def undo():
    data    = request.json or {}
    game_id = data.get('game_id')
    game    = get_game(game_id)
    if not game or len(game['history']) < 2:
        return jsonify({'error': 'Nothing to undo'}), 400

    # dropping the last ply (human + AI) and replaying history.
    # much easier than writing a reverse state transition for this board.
    history = game['history'][:-2]
    state   = GameState()
    for m in history:
        state = state.play(m)

    game['state']   = state
    game['history'] = history
    return jsonify({'state': state_to_dict(state)})

if __name__ == '__main__':
    print("\n  Ultimate Tic-Tac-Toe — HG-MCTS")
    print("  Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=False, port=5000)
