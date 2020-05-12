import numpy as np
import time
from boards import board_split_smart as board
from utils.clock import Clock
import operator

'''
The aim of this player : eat either human or ennemies if more unit
'''
SPLIT_SIZE = 2
TIME_LIMIT = 1.95
DEPTH = 5
SMART_SCAN_DEPTH = 10
C = 1  # constant used to emphasize some phenomenons


def getPositionsByOrder(positions, current_board, limit, depth):
    '''
    return position ordered by descending priority for tree search
    scores are computed by the function below. 
    We keep in memory scores of positions that we already explored 
    '''
    positions_scores = {}
    humans_memory = {}
    enemies_memory = {}
    for pos in positions:
        score = getOrderedScore(pos, current_board, depth, humans_memory, enemies_memory)
        positions_scores[str(pos)] = (score, pos)

    order = dict(sorted(positions_scores.items(), key=lambda kv: kv[1][0], reverse=True)[:limit]).values()
    return order


def getOrderedScore(positions, board, depth, humans_memory, ennemies_memory):
    '''
    positions refers to the potential new positions we could occupy in the next round 
    give bonuses to each position wrt to our ability to eat humans/ennemies in a close future 
    '''
    bonus = 0    
    
    humans_scores = []
    ennemies_scores = []
    
    eatable_humans = False
    eatable_ennemy = False
      
    for x, y, pos_nb in positions:
        
        # first type of bonus - if we eat enemies
        if ((x, y) in board.getOpponentCurrentPositions()):
            if (board.getOpponentDict()[(x, y)] * 1.5) <= pos_nb: #we are sure to win
                bonus += 1000 + board.getOpponentDict()[(x, y)]
            elif board.getOpponentDict()[(x, y)] <= pos_nb: # we have the avantage
                bonus += 10
            elif board.getOpponentDict()[(x, y)] >= pos_nb and board.getOpponentDict()[(x, y)] <= pos_nb * 1.5: # we have the avantage
                bonus += 1
            else: # we may not be dead but we loose units
                bonus -= 1000
        
        # second type - if we eat humans
        if ((x, y) in board.humansPos):
            if board.humansPos[(x, y)] <= pos_nb: #we are sure to win
                bonus += 100 + board.humansPos[(x, y)]
            else: # we might not be dead but loose units
                bonus -= 100
        
        ### perf 453 microsec

    
        #first type of bonus : we get closer to possibly eatable humans
        human_score = [0] #trick to ease process later on
        if (x, y, pos_nb) not in humans_memory:
           if len(board.humansPos) > 0 :
               positions_tile = np.tile([x, y], (len(board.humansPos), 1))
               humans = np.array(list(board.humansPos.keys()))
               distanceHumans = np.max(np.abs(positions_tile - humans), axis=1)
           
               # Study eatable humans and proximity 
               for dist, human_unit in zip(distanceHumans, board.humansPos.values()):
                   if(human_unit > pos_nb): 
                       p = pos_nb/(2*human_unit)
                       if p < 0.3: p=0 #if we risk to much, don't go
                   else: 
                       p = 1
                       eatable_humans=True
                   human_score.append(p * (human_unit) /(dist+1))
           humans_memory[(x, y, pos_nb)]=human_score
           
        humans_scores.append(humans_memory[(x, y, pos_nb)])
        
        #second type of bonus : we get closer to possibly eatable ennemies
        ennemy_score = [0] #trick to ease process later on
        if (x, y, pos_nb) not in ennemies_memory:
            if len(board.getOpponentDict()) > 0 :
                positions_tile = np.tile([x, y], (len(board.getOpponentDict()), 1))
                ennemy = np.array(list(board.getOpponentDict().keys()))
                distanceEnemies = np.max(np.abs(positions_tile - ennemy), axis=1)
            
                # Study eatable ennemies and proximity 
                for dist, enemy_unit in zip(distanceEnemies, board.getOpponentDict().values()):
                    if(enemy_unit >= pos_nb and enemy_unit < 1.5 * pos_nb):
                        eatable_ennemy=True
                        ennemy_score.append(1/(dist+1)) 
                    elif(enemy_unit >= 1.5 * pos_nb): 
                        ennemy_score.append(-C*np.abs(enemy_unit - pos_nb)/(dist+1))
                    elif (pos_nb > 1.5* enemy_unit): 
                        ennemy_score.append(C*np.abs(enemy_unit - pos_nb)/(dist+1))
                        eatable_ennemy=True
                    else: ennemy_score.append(np.abs(enemy_unit - pos_nb)/(dist+1))
            ennemies_memory[(x, y, pos_nb)]=ennemy_score
            
        ennemies_scores.append(ennemies_memory[(x, y, pos_nb)])
        
    
    #reduce by max humans and ennemy stats
    data = np.concatenate([np.array(ennemies_scores), np.array(humans_scores)], axis = 1)
    data = np.mean(data, axis = 0)
    bonus += np.sum(data)
     
    #######################################################################
    #### Defy death : attack humans and then ennemy if no chance to win ###
    #######################################################################   
    if len(positions) == 1 : # no split
        for x, y, pos_nb in positions:
            if ((x, y) in board.humansPos):
                # no easy eatable humans or ennemy 
                # and we are not splitting => maximizing our chance
                if not eatable_humans and not eatable_ennemy and len(board.humansPos) > 0:
                    bonus +=10000*depth #defy death
                    
            #if not eatable ennemy and no humans on board
                    #if we are not split
            if ((x, y) in board.getOpponentCurrentPositions()):
                if not eatable_ennemy or len(board.humansPos) == 0:
                    bonus +=10000*depth  #defy death
                
    ### perf 25.9 ms

    return bonus

def minimax(current_board, exploredPositions, heuristicHistory, clock, depth = DEPTH, 
            alpha = -10000000, beta = 10000000, isMax=True, histo_score = 0):
    '''
    perform tree search on a specific depth
    depth must be impair so that leaves are in maximize
    return the couple (best move, score)
    '''
    
    
    ########################
    ## process the leaves ##
    ########################
    if len(current_board.getCurrentPositions())==0: #no more positions, we are dead
        if isMax:
            return None, histo_score - 100000
        else:
            return None, histo_score + 100000
        
    if current_board.getOpponentUnitsNumberSum()==0: #no more positions, we win
        if isMax:
            return None, histo_score + 100000
        else:
            return None, histo_score - 100000
    
    if depth == 1: # if we have a simple tree of depth one
        return None, histo_score#getHeuristic(current_board, heuristicHistory)
    
    ###############################
    ## end of process the leaves ##
    ###############################

    possibleMoves = current_board.getAvailableMoves(SPLIT_SIZE)
    possibleMoves = getPositionsByOrder(possibleMoves, current_board,SMART_SCAN_DEPTH, depth)
    
    #dict to store results of leaf k: score, value : move
    scores = {}
    
    if isMax: #Maximizing player
        for score, target_pos in possibleMoves:
            # timeout
            if (clock.isTimeoutClose()):
                print('Timeout')
                if len(scores) > 0: #do we have results ?
                    return max(scores.values(), key=operator.itemgetter(1))
                else: #otherwise return big malus
                    return None, -100000

            minimax.nb_nodes_explore+=1 #stats
            
            new_board = current_board.generate_move(target_pos)
            #change player role for min player
            new_board.is_vampire = not current_board.is_vampire
            #compute current leaf score
            result = minimax(new_board, exploredPositions, heuristicHistory, clock, depth -1, 
                             alpha, beta, not isMax, histo_score + score * depth)
            scores[str(target_pos)] = (target_pos, result[1])
            #alpha beta pruning condition
            alpha = max(result[1], alpha)
            if alpha > beta:
                minimax.nb_cuts+=1 #stats
                break
        #if depth == DEPTH:
        #   print("scores", list(sorted(scores.values(), key=lambda kv: kv[1], reverse=True)))
        return max(scores.values(), key=operator.itemgetter(1))
    else: #Minimizing player
        for score, target_pos in possibleMoves:
            #timeout
            if(clock.isTimeoutClose()):
                print('Timeout')
                if len(scores) > 0 : #do we have results ?
                    return min(scores.values(), key=operator.itemgetter(1))
                else: #otherwise return big malus
                    return None, 100000

            minimax.nb_nodes_explore+=1 #stats
            
            new_board = current_board.generate_move(target_pos)
            #change player role for min player
            new_board.is_vampire = not current_board.is_vampire
            #compute current leaf score
            result = minimax(new_board, exploredPositions, heuristicHistory, clock, depth -1, 
                             alpha, beta, not isMax, histo_score)
            scores[str(target_pos)] = (target_pos, result[1])
            #alpha beta pruning condition
            beta = min(result[1], beta)
            if alpha > beta:
                minimax.nb_cuts+=1 #stats
                break
        return min(scores.values(), key=operator.itemgetter(1))
        

def run(sv):
    
    #initialize the board
    current_board = board.Board(sv.board_h, sv.board_w, sv.mapInfo, sv.startingPosition)
    status, updates = sv.update()
    current_board.updateBoard(updates)
    heuristicHistory = {}
    clock = Clock(TIME_LIMIT)
    while True:
        #print('Board :', current_board.getBoard())
        start_time = time.time()
        clock.startClock()
        minimax.nb_nodes_explore=0
        minimax.nb_cuts=0
        
        #perform tree search throw minimax and reprise optim pos
        exploredPositions = {}
        #current_pos = current_board.getCurrentPositions()
        #as new positions are sorted by pos number we do the same for the current_pos
        current_pos = list(dict(sorted(current_board.getOurDict().items(), 
                                  key=lambda kv: kv[1], reverse=True)).keys())
        
        new_pos = minimax(current_board, exploredPositions, heuristicHistory, clock)[0]
        
        #if we have more new pos than existing, this is a split to manage
        if len(new_pos) > len(current_pos):
            for i in range(len(new_pos) - len(current_pos)):
                current_pos.append(current_pos[0])
        print("current_pos", current_pos)
        print("new pos", new_pos)
        
        #move player
        sv.movePlayers_split(current_pos, new_pos)
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
    print('game ended')
    
    
def testGetOrderedScore_4():
    board_w, board_h = 10, 5
    vampires = {(4, 3): 4}
    humans = {(9, 0): 2, (2, 2): 4, (9, 2): 1, (9, 4): 10}
    cboard = board.Board(board_w, board_h, [], [])
    cboard.is_vampire = True
    cboard.humansPos = humans
    cboard.vampiresPos = vampires
    cboard.werewolvesPos = {(4, 1): 8}
    print(getPositionsByOrder([[[3, 3, 4]]], cboard, 4))

def testGetOrderedScore_5():
    board_w, board_h = 10, 5
    vampires = {(3, 3): 4}
    humans = {(9, 0): 2, (2, 2): 4, (9, 2): 1, (9, 4): 10}
    cboard = board.Board(board_w, board_h, [], [])
    cboard.is_vampire = True
    cboard.humansPos = humans
    cboard.vampiresPos = vampires
    cboard.werewolvesPos = {(4, 1): 8}
    print(getPositionsByOrder([[[2, 2, 4]]], cboard, 4)) 
    
def testGetOrderedScore_6():
    board_w, board_h = 10, 5
    vampires = {(4, 3): 4}
    humans = {(9, 0): 2, (2, 2): 4, (9, 2): 1, (9, 4): 10}
    cboard = board.Board(board_w, board_h, [], [])
    cboard.is_vampire = True
    cboard.humansPos = humans
    cboard.vampiresPos = vampires
    moves = cboard.getAvailableMoves(2)
    print(getPositionsByOrder(moves, cboard, -1))
    