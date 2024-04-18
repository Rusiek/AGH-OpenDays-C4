from app import (
    valid_moves,
    make_move_col,
    check_winner,
    evaluate,
    softmax
)
from copy import deepcopy
from tqdm import tqdm
import ray
import json

ray.init(ignore_reinit_error=True)

@ray.remote
def get_int(x):
    return x

@ray.remote
def minmax_remote(board, max_depth, player, curr_depth):
    if curr_depth == max_depth:
        return evaluate(board)
    
    moves = valid_moves(board)
    if not moves:
        return -1
    
    scores = []

    if player == 'ai':
        top_score = -10 ** 4
        for move in moves:
            board_copy = deepcopy(board)
            make_move_col(board_copy, move, 2)
            if check_winner(board_copy) == 2:
                return 10 ** 4
            score = minmax(board_copy, max_depth, 'human', curr_depth + 1)
            top_score = max(top_score, score)
            scores.append(score)
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
            scores.append(score)
        return top_score


def minmax(board, max_depth, player, curr_depth):
    if curr_depth == max_depth:
        return evaluate(board)
    
    moves = valid_moves(board)
    if not moves:
        return -1
    
    scores = []

    if player == 'ai':
        top_score = -10 ** 4
        for move in moves:
            board_copy = deepcopy(board)
            make_move_col(board_copy, move, 2)
            if check_winner(board_copy) == 2:
                return 10 ** 4
            score = minmax(board_copy, max_depth, 'human', curr_depth + 1)
            top_score = max(top_score, score)
            scores.append(score)
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
            scores.append(score)
        return top_score

data = {}

board = [[0 for _ in range(6)] for _ in range(7)]
MAX_DEPTH = 6
player = 'player'

queue = []
for col in range(7):
    new_board = deepcopy(board)
    make_move_col(new_board, col, 1)
    queue.append((new_board))

for x in tqdm(range(125 * 10 ** 2)):
    curr_board = queue.pop(0)
    hash_board = ''
    for row in curr_board:
        for cell in row:
            hash_board += str(cell)
    while hash_board in data:
        curr_board = queue.pop(0)
        hash_board = ''
        for row in curr_board:
            for cell in row:
                hash_board += str(cell)

    curr_board_2 = queue.pop(0)
    hash_board_2 = ''
    for row in curr_board_2:
        for cell in row:
            hash_board_2 += str(cell)
    while hash_board_2 in data or hash_board_2 == hash_board:
        curr_board_2 = queue.pop(0)
        hash_board_2 = ''
        for row in curr_board_2:
            for cell in row:
                hash_board_2 += str(cell)

    scores = []
    for col in range(7):
        new_board = deepcopy(curr_board)
        make_move_col(new_board, col, 2)
        if check_winner(new_board) == 2:
            scores.append(get_int.remote(10 ** 4))
        elif check_winner(new_board) == 1:
            scores.append(get_int.remote(-10 ** 4))
        else:
            score = minmax_remote.remote(new_board, MAX_DEPTH, 'human', 1)
            scores.append(score)

    for col in range(7):
        new_board = deepcopy(curr_board_2)
        make_move_col(new_board, col, 2)
        if check_winner(new_board) == 2:
            scores.append(get_int.remote(10 ** 4))
        elif check_winner(new_board) == 1:
            scores.append(get_int.remote(-10 ** 4))
        else:
            score = minmax_remote.remote(new_board, MAX_DEPTH, 'human', 1)
            scores.append(score)

    scores = ray.get(scores)
    scores_1 = scores[:7]
    scores_2 = scores[7:]

    data[hash_board] = [round(100 * score, 1) for score in softmax(scores_1)]
    for col in range(7):
        new_board = deepcopy(curr_board)
        make_move_col(new_board, col, 2)
        if check_winner(new_board) != 0:
            continue
        for new_col in range(7):
            new_board_2 = deepcopy(new_board)
            make_move_col(new_board_2, new_col, 1)
            if check_winner(new_board_2) != 0:
                continue
            queue.append(new_board_2)
    
    data[hash_board_2] = [round(100 * score, 1) for score in softmax(scores_2)]
    for col in range(7):
        new_board = deepcopy(curr_board_2)
        make_move_col(new_board, col, 2)
        if check_winner(new_board) != 0:
            continue
        for new_col in range(7):
            new_board_2 = deepcopy(new_board)
            make_move_col(new_board_2, new_col, 1)
            if check_winner(new_board_2) != 0:
                continue
            queue.append(new_board_2)
    
    if x % 100 == 0 and x != 0:
        with open('server/cache/data.json', 'w') as f:
            json.dump(data, f)
        
        max_cnt = 0
        for key, value in data.items():
            max_cnt = max(max_cnt, 42 - key.count('0'))
        print("IDX: ", x, "\nMAX TOKENS:", max_cnt)


with open('server/cache/data.json', 'w') as f:
    json.dump(data, f)

max_cnt = 0
for key, value in data.items():
    max_cnt = max(max_cnt, 42 - key.count('0'))
print("MAX TOKENS:", max_cnt)

# with open('server/cache/data.json', 'r') as f:
#     data = eval(f.read())
#     for key, value in data.items():
#         print(key, '\n', value)
#     print(data[((0, 0, 0, 0, 0, 1),
#                 (0, 0, 0, 0, 0, 0),
#                 (0, 0, 0, 0, 0, 0),
#                 (0, 0, 0, 0, 0, 0),
#                 (0, 0, 0, 0, 0, 0),
#                 (0, 0, 0, 0, 0, 0),
#                 (0, 0, 0, 0, 0, 0))])