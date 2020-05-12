import numpy as np
import time
from boards import board


def getPositionsByOrder(positions):
    '''
    return position ordered by descending priority for tree search
    '''
    return positions

def treeSearch(current_board):
    possibleMoves = current_board.getAvailableMoves()  # print 8 possible deplacement
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
        new_pos = [treeSearch(current_board)]
        print("new pos", new_pos)
        sv.movePlayers(current_board.getCurrentPositions(), current_board.getCurrentUnitsNumber(), new_pos)
        end_time = time.time()
        print("Time Elapsed : " + str(end_time - start_time))
        status, updates = sv.update()
        current_board.updateBoard(updates)
        if status == "END" or status == "BYE":
            break
        time.sleep(1)
    print('game ended')

