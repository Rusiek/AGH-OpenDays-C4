from flask import Flask, request, jsonify
from flask_cors import CORS  # Importujesz CORS
import random
from copy import deepcopy
import json


app = Flask(__name__)
CORS(app)  # Włączasz CORS dla całej aplikacji


def initialize_board(board):
    return deepcopy(board)


def valid_moves(board):
    return [c for c in range(7) if board[c][0] == 0]


def make_move_col(board, column, player):
    for r in range(5, -1, -1):
        if board[column][r] == 0:
            board[column][r] = player
            break


def check_winner(board):
    for c in range(7 - 3):
        for r in range(6):
            if board[c][r] != 0 and all(board[c + i][r] == board[c][r] for i in range(4)):
                return board[c][r]

    for c in range(7):
        for r in range(6 - 3):
            if board[c][r] != 0 and all(board[c][r + i] == board[c][r] for i in range(4)):
                return board[c][r]

    for c in range(7 - 3):
        for r in range(6 - 3):
            if board[c][r] != 0 and all(board[c + i][r + i] == board[c][r] for i in range(4)):
                return board[c][r]

    for c in range(3, 7):
        for r in range(6 - 3):
            if board[c][r] != 0 and all(board[c - i][r + i] == board[c][r] for i in range(4)):
                return board[c][r]

    return 0


@app.route('/move_random', methods=['POST'])
def make_move_A():
    data = request.get_json()
    board = data['board'][::-1]
    for line in board:
        print(line)
    
    available_columns = [i for i in range(7) if board[i][0] == 0]

    # log to console available columns
    print(available_columns)

    if available_columns:
        selected_column = random.choice(available_columns)
    else:
        selected_column = -1  # Brak dostępnych ruchów

    output = {
        'column': selected_column,
        'probabilities': [round(100 / len(available_columns), 1) if i in available_columns else 0 for i in range(7)],
        'win': '50:50',
    }

    return jsonify(output)


def evaluate_window(window):
    score = 0
    EMPTY = 0
    PLAYER = 1
    AI = 2
    if window.count(AI) == 4:
        score += 10 ** 4
    elif window.count(AI) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(AI) == 2 and window.count(EMPTY) == 2:
        score += 2
    elif window.count(PLAYER) == 2 and window.count(EMPTY) == 2:
        score -= 2
    elif window.count(PLAYER) == 3 and window.count(EMPTY) == 1:
        score -= 5
    elif window.count(PLAYER) == 4:
        score -= 10 ** -4
    return score


def evaluate(board):
    score = 0
    for c in range(7 - 3):
        for r in range(6):
            window = [board[c + i][r] for i in range(4)]
            score += evaluate_window(window)

    for c in range(7):
        for r in range(6 - 3):
            window = [board[c][r + i] for i in range(4)]
            score += evaluate_window(window)

    for c in range(7 - 3):
        for r in range(6 - 3):
            window = [board[c + i][r + i] for i in range(4)]
            score += evaluate_window(window)

    for c in range(3, 7):
        for r in range(6 - 3):
            window = [board[c - i][r + i] for i in range(4)]
            score += evaluate_window(window)

    return score


def minmax(board, max_depth, player, curr_depth):
    if curr_depth == max_depth:
        return evaluate(board)
    
    moves = valid_moves(board)
    if not moves:
        return -1

    if player == 'ai':
        top_score = -10 ** 4
        for move in moves:
            board_copy = deepcopy(board)
            make_move_col(board_copy, move, 2)
            if check_winner(board_copy) == 2:
                return 10 ** 4
            score = minmax(board_copy, max_depth, 'human', curr_depth + 1)
            top_score = max(top_score, score)
            #print(' ' * curr_depth, top_score)
        return top_score
    else:
        top_score = 10 ** 4
        for move in moves:
            board_copy = deepcopy(board)
            make_move_col(board_copy, move, 1)
            if check_winner(board_copy) == 1:
                return -10 ** 4
            score = minmax(board_copy, max_depth, 'ai', curr_depth + 1)
            top_score = min(top_score, score)
            #print(top_score)
        return top_score


def softmax(tab):
    tab = [x - max(tab) for x in tab]
    tab = [2.71828 ** x for x in tab]
    return [x / sum(tab) for x in tab]


@app.route('/move_minmax', methods=['POST'])
def make_move_B():
    data = request.get_json()
    board = data['board']
    for line in board:
        print(line)
    
    available_columns = [i for i in range(7) if board[i][0] == 0]
    MAX_DEPTH = data['power']
    scores = []
    for col in range(7):
        new_board = deepcopy(board)
        if col in available_columns:
            make_move_col(new_board, col, 2)
            if check_winner(new_board) == 2:
                scores.append(10 ** 4)
            else:
                scores.append(minmax(new_board, MAX_DEPTH, 'player', 1))
        else:
            scores.append(-10 ** 4)

    print(scores)
    top_score = max(scores)
    selected_column = scores.index(top_score)

    scores = softmax(scores)
    scores = [round(100 * score, 1) for score in scores]

    output = {
        'column': selected_column,
        'probabilities': scores
    }
    print(output)

    return jsonify(output)


@app.route('/move_minmax_cache', methods=['POST'])
def make_move_C():
    global cache
    data = request.get_json()
    board = data['board']
    for line in board:
        print(line)

    hash_board = ''
    for row in board:
        for cell in row:
            hash_board += str(cell)
    
    if hash_board in cache:
        scores = cache[hash_board]
        top_score = max(scores)
        selected_column = scores.index(top_score)
        scores = [round(score, 1) for score in scores]
        output = {
            'column': selected_column,
            'probabilities': scores,
        }
        return jsonify(output)
    
    available_columns = [i for i in range(7) if board[i][0] == 0]
    MAX_DEPTH = data['power']
    scores = []
    for col in range(7):
        new_board = deepcopy(board)
        if col in available_columns:
            make_move_col(new_board, col, 2)
            if check_winner(new_board) == 2:
                scores.append(10 ** 4)
            else:
                scores.append(minmax(new_board, MAX_DEPTH, 'player', 1))
        else:
            scores.append(-10 ** 4)

    print(scores)
    top_score = max(scores)
    selected_column = scores.index(top_score)

    scores = softmax(scores)
    scores = [round(100 * score, 1) for score in scores]

    output = {
        'column': selected_column,
        'probabilities': scores
    }
    print(output)
    cache[hash_board] = scores
    print('Updated cache')
    print(f'Size of cache: {len(cache)}')

    return jsonify(output)


if __name__ == '__main__':
    with open('server/cache/data.json', 'r') as f:
        cache = json.load(f)
    print(f'Size of cache: {len(cache)}')
    app.run(debug=True)
    
