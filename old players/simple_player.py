import numpy as np
import time
from boards import board

'''
The aim of this player is to play a simple strategy : go to the closest humans unit
'''


def getPositionsByOrder(positions):
    '''
    return position ordered by descending priority for tree search
    '''
    return positions

def minimax(current_board, depth = 5, alpha = -1000, beta = 1000, isMax=True):
    '''
    perform tree search on a specific depth
    depth must be impair so that leaves are in maximize
    return the couple (best move, score)
    '''
  
    if len(current_board.getCurrentPositions())==0: #no more positions, we are dead
        if isMax:
            return None, -1000
        else:
            return None, 1000
    
    if depth == 1:
        return None, getHeuristic(current_board)
    
    
    possibleMoves = current_board.getAvailableMoves()
    possibleMoves = getPositionsByOrder(possibleMoves)

    #dict to store results of leaf k: score, value : move
    scores = {}
    
    if isMax: #Maximizing player
        for target_pos in possibleMoves:
            minimax.nb_nodes_explore+=1 #stats
            
            new_board = current_board.generate_move(target_pos)
            #change player role for min player
            #print("Am I vampire?", current_board.is_vampire, "depth", depth)
            new_board.is_vampire = not current_board.is_vampire
            #compute current leaf score
            result = minimax(new_board, depth -1, alpha, beta, not isMax)
            scores[result[1]] = target_pos
            #alpha beta pruning condition
            alpha = max(result[1], alpha)
            if alpha > beta:
                minimax.nb_cuts+=1 #stats
                break
        result_key = max(scores.keys())
        return scores[result_key], result_key
    else: #Miximizing player
        for target_pos in possibleMoves:
            minimax.nb_nodes_explore+=1 #stats
            
            new_board = current_board.generate_move(target_pos)
            #change player role for min player
            #print("Am I vampire?", current_board.is_vampire, "depth", depth)
            new_board.is_vampire = not current_board.is_vampire
            #compute current leaf score
            result = minimax(new_board, depth -1, alpha, beta, not isMax)
            scores[result[1]] = target_pos
            #alpha beta pruning condition
            beta = min(result[1], beta)
            if alpha > beta:
                minimax.nb_cuts+=1 #stats
                break
        result_key = min(scores.keys())
        return scores[result_key], result_key
        

def run(sv):
    
    #initialize the board
    current_board = board.Board(sv.board_h, sv.board_w, sv.mapInfo, sv.startingPosition)   
    status, updates = sv.update()
    current_board.updateBoard(updates)
    
    while True:
        #print('Board :', current_board.getBoard())
        start_time = time.time()
        minimax.nb_nodes_explore=0
        minimax.nb_cuts=0
        
        #perform tree search throw minimax and reprise optim pos
        new_pos = [minimax(current_board)[0]]
        print("new pos", new_pos)
        
        #move player
        sv.movePlayers(current_board.getCurrentPositions(), current_board.getCurrentUnitsNumber(), new_pos)
        end_time = time.time()
        print("Time Elapsed : " + str(end_time - start_time))
        print("Number of nodes explored :", minimax.nb_nodes_explore)
        print("Number of cuts performed :", minimax.nb_cuts)
        
        status, updates = sv.update()
        #print("update", updates)
        current_board.updateBoard(updates)
        #print('new board', current_board.getBoard())
        
        #input('are you ready ?')
        if status == "END" or status == "BYE":
            break
        #time.sleep(1)
    print('game ended')
    
def getHeuristicFor(board):     
    position_x, position_y =  board.getCurrentPositions()[0]
    number = board.getCurrentUnitsNumber()[0]
    
    max_heuristic = 0
    for position in board.humansPos:
        if(number >= board.humansPos[position]):
            heuristic = board.humansPos[position] / (max(np.abs(position_x - position[0]), np.abs(position_y - position[1])) + 1)
            max_heuristic = max(max_heuristic, heuristic)
    
    #closest distance from ennemy + current_unit
    #print("heuristic value", max_heuristic + number)
    return max_heuristic + number

def getHeuristic(board):   
    #print('Board :', board.getBoard())
    our_unit_nb = board.getCurrentUnitsNumber()[0]
     
    humans_pos = np.array(list(board.humansPos.keys()),dtype=(int, int))
    humans_nb = np.array(list(board.humansPos.values()),dtype=int)
    
    #filter human position where we are not at least equal to them in number
    humans_pos = humans_pos[humans_nb <= our_unit_nb]
    humans_nb = humans_nb[humans_nb <= our_unit_nb]
    
    if len(humans_pos) > 0:    
        positions_tile = np.tile(board.getCurrentPositions()[0], (len(humans_pos), 1))
        #compute the distance with humans
        #print("positions_tile", positions_tile)
        #print("humans_pos", humans_pos)
        max_dist = np.max(np.abs(positions_tile - humans_pos), axis=1)
        max_heuristic_humans = humans_nb/ (max_dist + 1)
    else:
        max_heuristic_humans = [0]
    
    #our heuristic is human heuristic + our current unit_nb
    return max(max_heuristic_humans) + our_unit_nb
