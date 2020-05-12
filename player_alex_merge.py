import numpy as np
import time
from boards import board_split_smart as board
from utils.clock import Clock
import operator
import itertools

'''
The aim of this player : eat either human or ennemies if more unit
'''
SPLIT_SIZE = 2
TIME_LIMIT = 1.95
DEPTH = 5
SMART_SCAN_DEPTH = 4
MAX_SPLIT = 4
C = 3  # constant used to emphasize some phenomenons


def getPositionsByOrder(positions, current_board, limit, clock, depth):
    '''
    return position ordered by descending priority for tree search
    scores are computed by the function below. 
    We keep in memory scores of positions that we already explored 
    '''
    positions_scores = {}
    humans_memory = {}
    enemies_memory = {}
    for pos in positions:
        if (clock.isTimeoutClose()):
            print('Timeout')
            if len(positions_scores) == 0:
                positions_scores[str(positions[0])] = (0, positions[0])
            break
        score = SmartScan(pos, current_board, humans_memory, enemies_memory, depth)
        positions_scores[str(pos)] = (score, pos)

    #print(dict(sorted(positions_scores.items(), key=lambda kv: kv[1][0], reverse=True)))
    order = dict(sorted(positions_scores.items(), key=lambda kv: kv[1][0], reverse=True)[:limit]).values()
    return order


def SmartScan(positions, board, humans_memory, ennemies_memory, depth):
    '''
    positions refers to the potential new positions we could occupy in the next round 
    give bonuses to each position wrt to our ability to eat humans/ennemies in a close future 
    '''
    bonus = 0    
    merge_weight = 1
    
    humans_scores = []
    ennemies_scores = []
    considered_positions = []

    for x, y, pos_nb, w, z in positions:
         
        considered_positions.append([x, y])
        
        # First type of bonus - if we eat enemies
        if ((x, y) in board.getOpponentCurrentPositions()):
            if (board.getOpponentDict()[(x, y)] * 1.5) <= pos_nb: #we are sure to win
                bonus += 1000 + board.getOpponentDict()[(x, y)]
                pos_nb += board.getOpponentDict()[(x, y)]
            elif board.getOpponentDict()[(x, y)] <= pos_nb: # we have the avantage
                bonus += 1
            elif board.getOpponentDict()[(x, y)] >= 1.5 * pos_nb: # sure to loose
                bonus -= 1000
            else: # we may not be dead but we loose units
                bonus -= 1
                
        
        # Second type - if we eat humans
        if ((x, y) in board.humansPos):
            if board.humansPos[(x, y)] <= pos_nb: #we are sure to win
                bonus += 100 + board.humansPos[(x, y)]
                pos_nb += board.humansPos[(x, y)]
            else: # we might not be dead but loose units
                bonus -= 100
        
        ### perf 453 microsec
    
        # Third type of bonus : we get closer to possibly eatable humans
        human_score = [0] #trick to ease process later on
        if (x, y, pos_nb) not in humans_memory:
           if len(board.humansPos) > 0 :
               positions_tile = np.tile([x, y], (len(board.humansPos), 1))
               humans = np.array(list(board.humansPos.keys()))
               distanceHumans = np.max(np.abs(positions_tile - humans), axis=1)
           
                # ATTENTION 
                # The best version uses the function board.PotentialUnits(), that splits the map according to the direction you are taking
                # It also considers eatable humans more accurately, estimating potential units and taking into consideration ennemies positions
                # We did not have enough time to test it on every cases and therefore did not include it during the tournament, but it works better than current version
                """
                human_score.append(board.PotentialUnits(x, y, pos_nb, w, z))
                """

                # Study eatable humans and proximity 
                for dist, human_unit in zip(distanceHumans, board.humansPos.values()):
                    if(human_unit > pos_nb): p = 0.25*pos_nb/(2*human_unit)
                    else: p = 1
                    human_score.append(p * human_unit /(dist+1))
           humans_memory[(x, y, pos_nb)]=human_score
           
        humans_scores.append(humans_memory[(x, y, pos_nb)])
        

        # Forth type of bonus : we get closer to possibly eatable ennemies
        ennemy_score = [0] #trick to ease process later on
        if (x, y, pos_nb) not in ennemies_memory:
            if len(board.getOpponentDict()) > 0 :
                positions_tile = np.tile([x, y], (len(board.getOpponentDict()), 1))
                ennemy = np.array(list(board.getOpponentDict().keys()))
                distanceEnemies = np.max(np.abs(positions_tile - ennemy), axis=1)
            
                # Study eatable ennemies and proximity 
                for dist, enemy_unit in zip(distanceEnemies, board.getOpponentDict().values()):
                    if(enemy_unit > pos_nb and enemy_unit < 1.5 * pos_nb): 
                        if (sum(board.humansPos.values())==0 and len(board.getOurDict()) == 1): ennemy_score.append(5000/(dist+1))
                        else:
                            ennemy_score.append(-np.abs(enemy_unit - pos_nb)/(dist+1))
                    elif(enemy_unit >= 1.5 * pos_nb): 
                        if dist == 1: 
                            ennemy_score.append(-100*np.abs(enemy_unit - pos_nb)/(dist+1))
                        else: ennemy_score.append(-C*np.abs(enemy_unit - pos_nb)/(dist+1))
                    elif (pos_nb > 1.5* enemy_unit): ennemy_score.append(np.abs(enemy_unit - pos_nb)/(C*(dist+1)))
                    elif (enemy_unit == pos_nb): ennemy_score.append(1/(dist+1))
                    else: ennemy_score.append(np.abs(enemy_unit - pos_nb)/(C*(dist+1)))
            ennemies_memory[(x, y, pos_nb)]=ennemy_score
            
        ennemies_scores.append(ennemies_memory[(x, y, pos_nb)])
    

    
    # Last type of bonus - Merge case and end of game situation 
    humansLeft = sum(board.humansPos.values())
    nb_units = board.getOpponentUnitsNumberSum() + humansLeft + board.getCurrentUnitsNumberSum()
    if humansLeft + board.getOpponentUnitsNumberSum() < board.getCurrentUnitsNumberSum() or humansLeft < nb_units/20:
        if len(board.getOurDict()) > 1: # we are split USE NEW POSITION, NOT DICO len(considered_positions) > 1 
            inter_distance = 0
            for pos_pair in itertools.product(considered_positions, repeat=2):
                inter_distance += np.max(np.abs(np.array(pos_pair[0]) - np.array(pos_pair[1])))
            if(inter_distance > 0): bonus += 200/inter_distance
            else : bonus += 500
        else: # we a unique unit 
            distance_to_enemy = []
            distance_to_target = np.inf
            our_pos = considered_positions[0]
            for pos, numb in zip(board.getOpponentDict(), board.getOpponentUnitsNumber()): # change Dict Opponent 
                dist = np.max(np.abs(np.array(pos) - np.array(our_pos)))
                if 1.5*numb < board.getCurrentUnitsNumberSum(): 
                    distance_to_target = min(dist, distance_to_target)
                distance_to_enemy.append(dist)
            
            if distance_to_target != np.inf:   
                if depth == DEPTH: 
                    bonus += 10000 / (distance_to_target + 0.1)
            else: 
                distance_to_enemy = min(distance_to_enemy)
                bonus += 50 * distance_to_enemy
            

    # Reduce by max humans and ennemy stats
    data = np.concatenate([np.array(ennemies_scores), np.array(humans_scores)], axis = 1)
    data = np.mean(data, axis = 0)
    bonus += np.sum(data)

        
    ### perf 25.9 ms

    return bonus



def minimax(current_board, exploredPositions, heuristicHistory, clock, depth = DEPTH, 
            alpha = -1000000, beta = 1000000, isMax=True, histo_score = 0):
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
        return None, histo_score # histo_score is equivalent to getHeuristic(current_board, heuristicHistory)
    
    ###############################
    ## end of process the leaves ##
    ###############################

    #possibleMoves = current_board.getAvailableMoves(SPLIT_SIZE)
    possibleMoves = [current_board.getSplittingOptions(pos, MAX_SPLIT) for pos in current_board.getCurrentPositions()]
    possibleMovesFlat = []
    
    
    for k in list(itertools.product(*possibleMoves)):
        b = []
        for j in k:
            for i in j:
                b.append(i)
        possibleMovesFlat.append(b)
    if len(current_board.getOurDict()) <= MAX_SPLIT:
        truncatedPossibleMoves = [opt for opt in possibleMovesFlat if len(opt) <= MAX_SPLIT]
    else:
        truncatedPossibleMoves = possibleMovesFlat[:MAX_SPLIT]
    possibleMoves = getPositionsByOrder(truncatedPossibleMoves, current_board, SMART_SCAN_DEPTH, clock, depth)

    # dict to store results of leaf k: score, value : move
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
        sv.movePlayers_split_Leo(new_pos)
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
    