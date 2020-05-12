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
C = 2  # constant used to emphasize some phenomenons


def getPositionsByOrder(positions, current_board, limit, clock):
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
        score = getOrderedScore(pos, current_board, humans_memory, enemies_memory)
        positions_scores[str(pos)] = (score, pos)

    order = dict(sorted(positions_scores.items(), key=lambda kv: kv[1][0], reverse=True)[:limit]).values()
    return order



def getOrderedScore(positions, board, humans_memory, ennemies_memory):
    '''
    positions refers to the potential new positions we could occupy in the next round. It includes a move for each separated unit. 
    give bonuses to each position wrt to our ability to eat humans/ennemies in a close future 
    '''
    bonus = 0    
    merge_weight = 1
    s = sum(board.humansPos.values())
    
    humans_scores = []
    ennemies_scores = []
    pos_storage = []
    de = []
    min_de = []

    for x, y, pos_nb, w, z in positions:  # loop on units' potential future positions

        pos_storage.append([x,y]) # store move of each unit

        # 1st type of bonus - if we eat enemies
        if ((x, y) in board.getOpponentCurrentPositions()):
            if (board.getOpponentDict()[(x, y)] * 1.5) <= pos_nb: #we are sure to win
                bonus += 1000 + board.getOpponentDict()[(x, y)]
            elif board.getOpponentDict()[(x, y)] <= pos_nb: # we have the avantage
                bonus += 1
            else: # we may not be dead but we loose units
                bonus -= 1000
        
        # 2nd type - if we eat humans
        if ((x, y) in board.humansPos):
            if board.humansPos[(x, y)] <= pos_nb: #we are sure to win
                bonus += 100 + board.humansPos[(x, y)]
            else: # we might not be dead but loose units
                bonus -= 100
        
        ### perf 453 microsec


        # 3rd type of bonus : we get closer to possibly eatable humans
        total_units_nb = board.getCurrentUnitsNumberSum() 
        human_score = [0] #trick to ease process later on

        if (x, y, pos_nb) not in humans_memory:
            #if len(board.humansPos) > 0 :
                #positions_tile = np.tile([x, y], (len(board.humansPos), 1))
                #humans = np.array(list(board.humansPos.keys()))
        
            human_score = board.PotentialUnits(x, y, pos_nb, w, z)

            humans_memory[(x, y, pos_nb)]=human_score
        humans_scores.append(humans_memory[(x, y, pos_nb)])

        # When units are splitted, humans_scores does not have components of same size anymore because of PotentialUnits
        # These lines of code fix this pb by adding zeros when necessary
        b = np.zeros([len(humans_scores),len(max(humans_scores, key = lambda x: len(x)))])
        for i,j in enumerate(humans_scores):
            b[i][0:len(j)] = j
        humans_scores = b.tolist()


        # 4th type of bonus
        ennemy_score = [0] #trick to ease process later on
        if (x, y, pos_nb) not in ennemies_memory:
            if len(board.getOpponentDict()) > 0 :
                positions_tile = np.tile([x, y], (len(board.getOpponentDict()), 1)) 
                ennemy = np.array(list(board.getOpponentDict().keys()))
                distanceEnemies = np.max(np.abs(positions_tile - ennemy), axis=1) # list distance with enemies
                
                # Study eatable ennemies and proximity 
                for dist, enemy_unit in zip(distanceEnemies, board.getOpponentDict().values()):
                    if pos_nb < 1.5 * enemy_unit: de.append(dist) 
                    if(enemy_unit > pos_nb and enemy_unit < 1.5 * pos_nb): 
                        if (s ==0): ennemy_score.append(1/(dist+1)) 
                        else:
                            ennemy_score.append(-np.abs(enemy_unit - pos_nb)/(dist+1))
                    elif(enemy_unit >= 1.5 * pos_nb): ennemy_score.append(-C*np.abs(enemy_unit - pos_nb)/((dist+1)))
                    elif (pos_nb > 1.5* enemy_unit): ennemy_score.append(np.abs(enemy_unit - pos_nb)/(C*(dist+1)))
                    elif (enemy_unit == pos_nb): ennemy_score.append(1/(dist+1))
                    else: ennemy_score.append(np.abs(enemy_unit - pos_nb)/(dist+1))
                
            ennemies_memory[(x, y, pos_nb)]=ennemy_score
            
        ennemies_scores.append(ennemies_memory[(x, y, pos_nb)])
         
        # Store distance of closest enemy that could kill us
        if (de != []): min_de.append(min(de))
        
    # reduce by max humans and ennemy stats
    data = np.concatenate([np.array(ennemies_scores), np.array(humans_scores)], axis = 1)
    data = np.mean(data, axis = 0) # average score of each split unit created
    bonus += np.sum(data)
    
    
    # 5th type of bonus - strongly encourage units to merge when there is no human left 
    # We compute the pairwise distance between each unit's new position
    '''
    if s == 0:
        intra_dist = []
        for i in range(len(pos_storage)): 
            loc = pos_storage[i]
            intra_dist.append([np.max(np.abs(loc - item), axis=1) for item in pos_storage[i+1:]])  
        print('intra dist', intra_dist)
        bonus += 1000 / (sum(intra_dist) + 1)
    '''
    
    # Incentive to merge when there are not many humans left and that enemy get close to us
    nb_units = board.getOpponentUnitsNumberSum() + s + board.getCurrentUnitsNumberSum()
    if s < nb_units/15:
        print('CASE 1, we are in the case where you would like to regroup')
        intra_dist = 0
        for i in range(len(pos_storage)): 
            loc = pos_storage[i]
            intra_dist += sum([np.max(np.abs(np.array(loc) - np.array(item))) for item in pos_storage[i+1:]])
            # intra_dist.append([np.max(np.abs(np.array(loc) - np.array(item))) for item in pos_storage[i+1:]])
            print('intra dist', intra_dist)
        #bonus += 1000 / (intra_dist + 1) 
        bonus += 50 * intra_dist * len(pos_storage)
    else:  # incentive to split otherwise
        print('usual case')
        intra_dist = 0
        for i in range(len(pos_storage)): 
            loc = pos_storage[i]
            intra_dist += sum([np.max(np.abs(np.array(loc) - np.array(item))) for item in pos_storage[i+1:]])
            # intra_dist.append([np.max(np.abs(np.array(loc) - np.array(item))) for item in pos_storage[i+1:]])
            print('intra dist', intra_dist)
        #bonus += 1000 / (intra_dist + 1) 
        bonus += intra_dist * len(pos_storage)
        
    if (min_de != []):
        if min(min_de) < 2: 
            print('CASE 2 we are in the case where you would like to regroup')
            intra_dist = 0
            for i in range(len(pos_storage)): 
                loc = pos_storage[i]
                intra_dist += sum([np.max(np.abs(np.array(loc) - np.array(item))) for item in pos_storage[i+1:]])
                print(intra_dist)
                # intra_dist.append([np.max(np.abs(np.array(loc) - np.array(item))) for item in pos_storage[i+1:]])
                print('intra dist', intra_dist)
            bonus -= 50 * intra_dist * len(pos_storage) 
            #bonus += 100 / (sum(intra_dist) + 1)  # reduce impact, might be counted several times accross branches
     
    # As it is used during tree search, be careful to its implementation. 
    # Otherwise put an extra condition on the Depth 


    #penalyze a bit split to facilitate merge
    #TODO correct as merge is performed later
    #bonus -= (len(board.getCurrentPositions())-1) * merge_weight
        
    ### perf 25.9 ms

    # return score of this move (combined score of each unit's deplacement)
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
        return None, histo_score #getHeuristic(current_board, heuristicHistory)
    
    ###############################
    ## end of process the leaves ##
    ###############################

    
    # Find all possible moves (split included) for each unit. Gives a list of list (units) of list (pos)
    possibleMoves = [current_board.getSplittingOptions(pos, MAX_SPLIT) for pos in current_board.getCurrentPositions()]
    possibleMovesFlat = []
    
    # Consider all potential combinations of possible moves across units
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

    # Keep only best moves to consider in tree search
    possibleMoves = getPositionsByOrder(truncatedPossibleMoves, current_board, SMART_SCAN_DEPTH, clock)

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
        #    print("scores", list(sorted(scores.values(), key=lambda kv: kv[1], reverse=True)))
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
    

def testGetOrderedScore_1():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 14, (3, 3) : 18}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    cboard = board.Board(board_w, board_h, [], [])
    cboard.is_vampire = True
    cboard.humansPos = humans
    cboard.vampiresPos = vampires
    cboard.werewolvesPos = {(1, 2) : 7, (1, 3) : 7}
    moves = cboard.getAvailableMoves(1)
    print(getPositionsByOrder(moves, cboard, 4))
    
def testGetOrderedScore_2():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 14, (3, 3) : 18}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    cboard = board.Board(board_w, board_h, [], [])
    cboard.is_vampire = True
    cboard.humansPos = humans
    cboard.vampiresPos = vampires
    cboard.werewolvesPos = {(1, 2) : 7, (1, 3) : 7}
    moves = cboard.getAvailableMoves(2)
    print(getPositionsByOrder(moves, cboard, 4))
    
def testGetOrderedScore_3():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 4}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    cboard = board.Board(board_w, board_h, [], [])
    cboard.is_vampire = True
    cboard.humansPos = humans
    cboard.vampiresPos = vampires
    cboard.werewolvesPos = {(1, 2) : 7, (1, 3) : 7}
    moves = cboard.getAvailableMoves(3)
    print(getPositionsByOrder(moves, cboard,4))
    
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
    