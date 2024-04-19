from flask import Flask, request, jsonify
from flask_cors import CORS  # Importujesz CORS
import random
from copy import deepcopy
import json
from time import time
from math import log2, sqrt


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


def evaluate_window(window, binary=False):
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
    if binary:
        if score == 10 ** 4 or score == -10 ** 4:
            return score
    return score


def evaluate(board, binary=False):
    score = 0
    for c in range(7 - 3):
        for r in range(6):
            window = [board[c + i][r] for i in range(4)]
            score += evaluate_window(window, binary)

    for c in range(7):
        for r in range(6 - 3):
            window = [board[c][r + i] for i in range(4)]
            score += evaluate_window(window, binary)

    for c in range(7 - 3):
        for r in range(6 - 3):
            window = [board[c + i][r + i] for i in range(4)]
            score += evaluate_window(window, binary)

    for c in range(3, 7):
        for r in range(6 - 3):
            window = [board[c - i][r + i] for i in range(4)]
            score += evaluate_window(window, binary)

    return score


def minmax(board, max_depth, player, curr_depth, alpha, beta):
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


def minmaxscaler(tab, b):
    return [(x - min(tab)) / (max(tab) - min(tab)) for x in tab]


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
            elif check_winner(new_board) == 1:
                scores.append(-10 ** 4)
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
            elif check_winner(new_board) == 1:
                scores.append(-10 ** 4)
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


class MockMCTS:
    def __init__(self, board, who_won=None, root=None, player=None):
        self.board = board
        self.root = root
        self.visits = 1
        self.wins = 0
        self.losses = 0
        self.player = player
        if who_won == "AI":
            self.wins = 1
            self.losses = 0
        if who_won == "Player":
            self.wins = 0
            self.losses = 1
        if who_won == "Draw":
            self.wins = 0
            self.losses = 0
    
    def simulate_one_game(self):
        self.backpropagate("AI" if check_winner(self.board) == 2 else "Player")

    def backpropagate(self, win):
        self.visits += 1
        if win == "AI":
            self.wins += 1
        elif win == "Player":
            self.losses += 1

        if self.root:
            self.root.backpropagate(win)


class MCTS:
    def __init__(self, board, player, root=None, runtime=None, games=None):
        self.root = root
        self.board = deepcopy(board)
        self.player = player
        self.children = []
        self.visits = 0
        self.wins = 0
        self.losses = 0
        self.runtime = runtime
        self.games = games


    def select(self):
        return max(self.children, key=lambda child: child.wins / (child.visits + 1) + sqrt(2 * log2(self.visits + 1) / (child.visits + 1)) if child.losses >= 0 else -1)


    def expand(self):
        if not self.children:
            for col in range(7):
                new_board = deepcopy(self.board)
                if col in valid_moves(self.board):
                    make_move_col(new_board, col, self.player)
                    winner = check_winner(new_board)
                    if check_winner(new_board):
                        self.children.append(MockMCTS(new_board, who_won=winner, root=self, player=1 if self.player == 2 else 2))
                    else:
                        self.children.append(MCTS(new_board, 2 if self.player == 1 else 1, root=self))
                elif self.root == None:
                    self.children.append(MockMCTS(new_board, root=self, player=1 if self.player == 2 else 2))


    def simulate(self):
        if self.runtime:
            start_time = time()
            while time() - start_time < self.runtime:
                self.simulate_one_game()
        else:
            for _ in range(self.games):
                self.simulate_one_game()
                

    def simulate_one_game(self):
        self.expand()
        child = self.select()
        board = deepcopy(child.board)
        player = child.player

        while not check_winner(board) and valid_moves(board):
            make_move_col(board, random.choice(valid_moves(board)), player)
            player = 1 if player == 2 else 2

        winner = check_winner(board)
        if winner == 2:
            child.backpropagate("AI")
            return
        elif winner == 1:
            child.backpropagate("Player")
            return
        child.backpropagate("Draw")


    def backpropagate(self, win):
        self.visits += 1
        if win == "AI":
            self.wins += 1
        elif win == "Player":
            self.losses += 1
        
        if self.root:
            self.root.backpropagate(win)


    def get_probabilities(self):
        print([(child.wins, child.losses, child.visits) for child in self.children])
        return [(child.wins + 1) / (child.visits + 1) if child.visits else 0 for child in self.children]


@app.route('/move_monte_carlo', methods=['POST'])
def make_move_D():
    data = request.get_json()
    board = data['board']
    power = data.get('power', 100)
    runtime = data.get('runtime', None)
    for line in board:
        print(line)
    print(power, runtime)
    mcts = MCTS(board, 2, games=power, runtime=runtime)
    mcts.simulate()
    scores = mcts.get_probabilities()
    print(scores)
    top_score = max(scores)
    selected_column = scores.index(top_score)
    if selected_column not in valid_moves(board):
        selected_column = random.choice(valid_moves(board))

    scores = [round(100 * score, 1) for score in scores]

    output = {
        'column': selected_column,
        'probabilities': scores
    }
    print(output)

    return jsonify(output)


if __name__ == '__main__':
    with open('server/cache/data.json', 'r') as f:
        cache = json.load(f)
    print(f'Size of cache: {len(cache)}')
    app.run(debug=True)
    
