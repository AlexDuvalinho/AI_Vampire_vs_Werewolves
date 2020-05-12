import numpy as np
import time
from boards import board
from utils.clock import Clock
import operator

'''
The aim of this player : eat either human or ennemies if more unit
'''



def getPositionsByOrder(positions, current_board, exploredPositions):
    '''
    return position ordered by descending priority for tree search
    scores are computed by the function below. 
    We keep in memory scores of positions that we already explored 
    '''
    positions_scores = {}
    for pos in positions:
        if(tuple(pos) in exploredPositions):
            positions_scores[tuple(pos)] = exploredPositions[tuple(pos)]
        else:
            score = getOrderedScore(pos, current_board)
            positions_scores[tuple(pos)] = score
            exploredPositions[tuple(pos)] = score 

    return dict(sorted(positions_scores.items(), key=lambda kv: kv[1], reverse=True)).keys()



# Useless now 
def getOrderedScore(position, board):
    '''
    position refers to one of the potential new positions we could occupy in the next round 
    give bonuses to each position wrt to our ability to eat humans/ennemies in a close future 
    '''
    bonus = 0
    my_unit = board.getBiggestPosition()[1]

    # first type of bonus - if we eat enemies
    if (tuple(position) in board.getOpponentCurrentPositions()):
        if board.getOpponentDict()[tuple(position)] <= board.getBiggestPosition()[1]:
            bonus += 1000 * board.getOpponentDict()[tuple(position)]
    
    # second type - if we eat humans
    if (tuple(position) in board.humansPos):
        if board.humansPos[tuple(position)] <= board.getBiggestPosition()[1]:
            bonus += 100 * board.humansPos[tuple(position)]

    # third type of bonus : we get closer to possibly eatable humans or enemies
    eatable = [k for k, v in board.humansPos.items() if my_unit >= v] + [k for k, v in board.getOpponentDict().items()
                                                                         if my_unit >= 1.5 * v]
    if len(eatable) > 0:
        maxDistance = max(board.board_w, board.board_h) 
        maxNumber = board.getOpponentUnitsNumberSum() + sum(list(board.humansPos.values()))
        distance = [10 - 9 * np.max(np.abs(np.subtract(list(enemy), position))) / maxDistance for enemy in eatable]
        number = [9 * unit / maxNumber for unit in board.humansPos.values() if my_unit >= unit] + [9 * unit / maxNumber for
                                                                                                   unit in
                                                                                                   board.getOpponentUnitsNumber()
                                                                                                   if my_unit >= 1.5 * unit]
        combined = [10 * dist + num for dist, num in zip(distance, number)]
        bonus += (maxDistance - np.min(combined))

    return bonus


def getSmartAvailableMoves(board, size, split=False):
        '''
            Orders the positions we can move to in a list, where the first one has the highest score 
            It should be explored first during the Tree Search 
        '''
        originalPositions = board.getAvailableMoves(split)
        size = min(size, len(originalPositions))
        scoreDict = {}
        # evaluate the score for each position
        for unit in board.getCurrentUnitsNumber():
            for position in originalPositions:
                scoreDict[tuple(position)] = getAvailableMovesScore(board, position, unit)
        # return only the n best positions
        sortedDict = sorted(scoreDict, key = scoreDict.get, reverse = True)
        sortedList = list(map(list, sortedDict))[:size]
        return sortedList


def getAvailableMovesScore(board, position, unit):
        '''
        compute a score that defines how desirable each position is given how many units you can eat for certain and when (time - dist)
        '''
        eatableOpponents = [k for k in board.humansPos if unit >= board.humansPos[k]] + [k for k in board.getOpponentDict() if unit >= 1.5*board.getOpponentDict()[k]]
        number = [u for u in board.humansPos.values() if unit >= u] + [u for u in board.getOpponentUnitsNumber() if unit >= 1.5 * u]
        distance = [np.max(np.abs(np.subtract(list(enemy), position))) for enemy in eatableOpponents]
        score = np.sum([n/(d+1) for n, d in zip(number, distance)])
        return score


def minimax(current_board, exploredPositions, heuristicHistory, clock, depth = 5, alpha = -1000, beta = 1000, isMax=True):
    '''
    perform tree search on a specific depth
    depth must be impair so that leaves are in maximize
    HeuristicHistory stores all heuristics previously computed for each position of the board
    return the couple (best move, score)
    '''
    ########################
    ## process the leaves ##
    ########################
    if len(current_board.getCurrentPositions())==0: #no more positions, we are dead
        if isMax:
            return None, -1000
        else:
            return None, 1000
        
    if current_board.getOpponentUnitsNumberSum()==0: #no more positions, we win
        if isMax:
            return None, 1000
        else:
            return None, -1000
    
    if depth == 1: # if we have a simple tree of depth one
        return None, getHeuristic(current_board, heuristicHistory)
    
    ###############################
    ## end of process the leaves ##
    ###############################
    
    
    # Smart scan only for the first level of the tree
    """
    if depth == 5: 
        possibleMoves = getSmartAvailableMoves(current_board, size=4)
        possibleMoves = getPositionsByOrder(possibleMoves, current_board, exploredPositions)
    else: 
        possibleMoves = current_board.getAvailableMoves()
        possibleMoves = getPositionsByOrder(possibleMoves, current_board, exploredPositions)
    """
    
    # smart scan at each level of the tree
    possibleMoves = getSmartAvailableMoves(current_board, size=4)
    possibleMoves = getPositionsByOrder(possibleMoves, current_board, exploredPositions)
    

    #dict to store results of leaf k: score, value : move
    scores = {}
    
    if isMax: #Maximizing player
        for target_pos in possibleMoves:
            # timeout
            if (clock.isTimeoutClose()):
                print('Timeout')
                if len(scores) > 0: #do we have results ?
                    return max(scores.items(), key=operator.itemgetter(1))
                else: #otherwise return big malus
                    return None, -1000

            minimax.nb_nodes_explore+=1 #stats
            
            new_board = current_board.generate_move(target_pos)
            #change player role for min player
            new_board.is_vampire = not current_board.is_vampire
            #compute current leaf score
            result = minimax(new_board, exploredPositions, heuristicHistory, clock, depth -1, 
                             alpha, beta, not isMax)
            scores[target_pos] = result[1]
            #alpha beta pruning condition
            alpha = max(result[1], alpha)
            if alpha > beta:
                minimax.nb_cuts+=1 #stats
                break
        return max(scores.items(), key=operator.itemgetter(1))
    else: #Minimizing player
        for target_pos in possibleMoves:
            #timeout
            if(clock.isTimeoutClose()):
                print('Timeout')
                if len(scores) > 0 : #do we have results ?
                    return min(scores.items(), key=operator.itemgetter(1))
                else: #otherwise return big malus
                    return None, 1000

            minimax.nb_nodes_explore+=1 #stats
            
            new_board = current_board.generate_move(target_pos)
            #change player role for min player
            new_board.is_vampire = not current_board.is_vampire
            #compute current leaf score
            result = minimax(new_board, exploredPositions, heuristicHistory, clock, depth -1, alpha, beta, not isMax)
            scores[target_pos] = result[1]
            #alpha beta pruning condition
            beta = min(result[1], beta)
            if alpha > beta:
                minimax.nb_cuts+=1 #stats
                break
        return min(scores.items(), key=operator.itemgetter(1))
        

def run(sv):
    
    #initialize the board
    current_board = board.Board(sv.board_h, sv.board_w, sv.mapInfo, sv.startingPosition)
    status, updates = sv.update()
    current_board.updateBoard(updates)
    
    heuristicHistory = {}
    clock = Clock(1.95)
    while True:
        #print('Board :', current_board.getBoard())
        start_time = time.time()
        clock.startClock()
        minimax.nb_nodes_explore=0
        minimax.nb_cuts=0
        
        #perform tree search throw minimax and reprise optim pos
        exploredPositions = {}
        new_pos = [minimax(current_board, exploredPositions, heuristicHistory, clock)[0]]
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
    

def getHeuristic(board, heuristicHistory):
    hash = board.hash()
    if (hash in heuristicHistory):
        heuristic = heuristicHistory[hash]
    else:
        #print('Board :', board.getBoard())
        our_position, our_unit_nb = board.getBiggestPosition()
        opponents_unit_nb = board.getOpponentUnitsNumberSum()

        humans_pos = np.array(list(board.humansPos.keys()),dtype=(int, int))
        humans_nb = np.array(list(board.humansPos.values()),dtype=int)

        enemy_pos = np.array(board.getOpponentCurrentPositions(),dtype=(int, int))
        enemy_nb = np.array(board.getOpponentUnitsNumber(),dtype=int)

        #filter human positions where we are not at least equal to them in number
        humans_pos = humans_pos[humans_nb <= our_unit_nb]
        humans_nb = humans_nb[humans_nb <= our_unit_nb]

        #filter enemy positions where we are 1.5x more so we are sure to win
        enemy_pos = enemy_pos[enemy_nb * 1.5 <= our_unit_nb]
        enemy_nb = enemy_nb[enemy_nb * 1.5 <= our_unit_nb]

        if len(humans_pos) > 0:
            positions_tile = np.tile(our_position, (len(humans_pos), 1)) # create an array of our_position, reapeated human_pos times
            #compute the distance with humans (and our position)
            max_dist = np.max(np.abs(positions_tile - humans_pos), axis=1)
            max_heuristic_humans = humans_nb/ (max_dist + 1)
        else:
            max_heuristic_humans = [0]

        if len(enemy_pos) > 0:
            positions_tile = np.tile(our_position, (len(enemy_pos), 1))
            #compute the distance with ennemy
            max_dist = np.max(np.abs(positions_tile - enemy_pos), axis=1)
            max_heuristic_enemy = enemy_nb/ (max_dist + 1)
        else:
            max_heuristic_enemy = [0]

        #our heuristic is human heuristic + enemy heuristic + our current unit_nb - enemy unit number
        #print(board.getBiggestPosition())
        #print("max(max_heuristic_humans)", max(max_heuristic_humans),
        #      "max_heuristic_enemy", max_heuristic_enemy,
        #      "max(max_heuristic_enemy)" , max(max_heuristic_enemy))
        heuristic = max(max_heuristic_humans) + max(max_heuristic_enemy) + our_unit_nb - opponents_unit_nb
        #print(heuristic)
        heuristicHistory[hash] = heuristic
    return heuristic

