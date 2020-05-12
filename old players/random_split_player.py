import numpy as np
import time
from boards import board
import itertools



def getPositionsByOrder(positions):
    '''
    return position ordered by descending priority for tree search
    '''
    return positions

def getAvailableMoves(board, split = 2):
    nb = board.getBiggestPosition()[1]
    
    mono_positions = board.getAvailableMoves()
    
    if nb == 1 : # we can't perform split
        units = [1 for x in mono_positions]
        mono_positions = [[pos] for pos in mono_positions]
        return list(zip(mono_positions, units))
    
    else :
        duo_pos = list(itertools.permutations(mono_positions, split))
        #
        first = [nb//2 for x in mono_positions]
        second = nb - first
        
        return list(zip(duo_pos, first, second))

def treeSearch(current_board):
    possibleMoves = getAvailableMoves(current_board)  # print 8 possible deplacement
    possibleMoves = getPositionsByOrder(possibleMoves) # does nothing special

    scores = []
    for move in possibleMoves:
        scores.append(getScore(move))
    return possibleMoves[np.argmax(scores)]

def getScore(position):
    return np.random.randint(0, 100)  # simply assign a random number, no heuristic 

def testTreeSearch():
    print(treeSearch([2, 2], 3, 3))

def run(sv):
    
    #initialize the board
    current_board = board.Board(sv.board_h, sv.board_w, sv.mapInfo, sv.startingPosition)   
    status, updates = sv.update()
    current_board.updateBoard(updates)
    
    while True:
        #print('Board :', current_board.getBoard())
        print(sv.board_h, sv.board_w)
        start_time = time.time()
        new_pos = treeSearch(current_board)
        print("new pos", new_pos)
        
        current_pos = [current_board.getBiggestPosition()[0] for i in new_pos[1:]]
        
        sv.movePlayers(current_pos, new_pos[1:], new_pos[0])
        end_time = time.time()
        print("Time Elapsed : " + str(end_time - start_time))
        status, updates = sv.update()
        current_board.updateBoard(updates)
        if status == "END" or status == "BYE":
            break
        time.sleep(1)
    print('game ended')

