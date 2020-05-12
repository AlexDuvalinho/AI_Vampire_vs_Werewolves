import numpy as np
import time
from boards import board
from utils.clock import Clock
import operator

'''
The aim of this player : eat either human or ennemies if more unit
'''

def getPositionsScores(positions, current_board, exploredPositions):
    '''
    Returns score associated with each positions 
    '''
    return list(positions.values())


def getPositionsByOrder(positions, current_board, exploredPositions):
    '''
    return position ordered by descending priority for tree search
    scores are computed by the function below. 
    We keep in memory scores of positions that we already explored 
    '''
    return positions.keys()


def getSmarterAvailableMoves(board, size, split = False):
        '''
        attributes a score to each potential move we can make
        This score takes into an up-to-date number of humans as we will move across the map and the ennemies
        deals with the split
        Returns a dictionnary sorted by score (value), where the key is the position investigated
        '''
        Positions = board.getAvailableMoves(split)

        size = min(size, len(Positions))  # how many positions we return 
        scoreDict = {}
        unit = board.getBiggestPosition()[1] # for split, do a loop 
        
        for position in Positions: # loop through possible positions (for one unit)
            score = 0

            # if humans are on our next potential position 
            if(tuple(position) in board.humansPos): 
                if(board.humansPos[tuple(position)] > unit): # don't want to go if they are more than us 
                    score = -100
                else:
                    score += 50 + 5 * board.humansPos[tuple(position)] # give incentive to go eat asap
            
            # if ennemy are on our next potential position 
            if (tuple(position) in board.getOpponentDict()):  
                if (board.getOpponentDict().get(tuple(position)) > 1.5 * unit): 
                    score -= 500  
                if (board.getOpponentDict().get(tuple(position)) > unit): 
                    score += 10  
                else:
                    score += 500


            # Compute key metrics about us 
            # distanceHumans = [np.max(np.abs(np.subtract(list(human), position))) for human in board.humansPos]
            distanceEnemies = [np.max(np.abs(np.subtract(list(enemy), position))) for enemy in board.getOpponentDict()]
            total_units_nb = board.getCurrentUnitsNumberSum() 
            potential_units = unit 
            
            # Call function - takes into account potential number of units and distance to ennemies 
            score = board.PotentialUnits(score, position, potential_units)

            # Study eatable ennemies and proximity 
            weight_dist = 5
            for dist, enemy_unit in zip(distanceEnemies, board.getOpponentDict().values()):
                if(enemy_unit >= 1.5 * total_units_nb): score -= (enemy_unit - total_units_nb)/weight_dist*(dist+1) # avoid 
                elif (total_units_nb > 1.5* enemy_unit): score += (total_units_nb - enemy_unit)/weight_dist*(dist+1) # go towards 
                else: score += 1/weight_dist*(dist+1)  # if no humans left, go attack 
                                    

            scoreDict[tuple(position)] = score
        sortedDict = dict(sorted(scoreDict.items(), key=lambda kv: kv[1], reverse=True)[:size]) # dico with value=score, key:position
        #sortedScores = sorted(scoreDict.values(), reverse=True)[:size]
        # sortedPos = sorted(scoreDict, key=scoreDict.get, reverse=True)[:4] # sort the dictionnary by score
        # sortedList = list(map(list, sortedDict))[:4] # list best potential positions, by order in format [[i,j],...]
        return sortedDict  




def minimax(current_board, exploredPositions, heuristicHistory, possibleMovesScores, possibleMovesScores5, Smart_score, clock, depth = 5, alpha = -1000, beta = 1000, isMax=True):
    '''
    perform tree search on a specific depth
    depth must be impair so that leaves are in maximize
    HeuristicHistory stores all heuristics previously computed for each position of the board
    return the couple (best move, score)
    '''
    ########################
    ## process the leaves ##
    ########################
    if len(current_board.getCurrentPositions())==0: # we don't have anymore position, meaning we are dead
        if isMax:
            return None, -1000
        else:
            return None, 1000
        
    if current_board.getOpponentUnitsNumberSum()==0: #the opponent does not have anymore units, we win
        if isMax:
            return None, 1000
        else:
            return None, -1000
    
    if depth == 1: # if we have a simple tree of depth one
        #print('heuristic', Smart_score)
        return None, getHeuristic(current_board, heuristicHistory, Smart_score)
    
    ###############################
    ## end of process the leaves ##
    ###############################
    
    # Smart scan only for the first level of the tree
    """
    if depth == 5: 
        possibleMoves = getSmarterAvailableMoves(current_board, size=4)
        possibleMoves = getPositionsByOrder(possibleMoves, current_board, exploredPositions)
    else: 
        possibleMoves = current_board.getAvailableMoves()
        possibleMoves = getPositionsByOrder(possibleMoves, current_board, exploredPositions)
    """

    # Only consider the smart possible moves in the tree 
    possibleMoves = getSmarterAvailableMoves(current_board, 4)

    # Store the smart score associated with each position 
    if depth == 5:
        possibleMovesScores5.append(getPositionsScores(possibleMoves, current_board, exploredPositions))
        possibleMovesScores5 = [j for i in possibleMovesScores5 for j in i]
        #print('depth 5 scores: ', possibleMovesScores5)
    if depth ==3:
        possibleMovesScores = []
        possibleMovesScores.append(getPositionsScores(possibleMoves, current_board, exploredPositions)) # id fct
        possibleMovesScores = [j for i in possibleMovesScores for j in i]
        #print('depth 3 scores:  ', possibleMovesScores)
    
    # keep only the position
    possibleMoves = getPositionsByOrder(possibleMoves, current_board, exploredPositions)  # id fct 

    #dict to store results of leaf k: score, value : move
    scores = {}
    
    if isMax: #Maximizing player
        for target_pos in possibleMoves:  # 1st branch of the tree, depth 1. 
            
            if depth ==5: 
                del possibleMovesScores5[0]
                Smart_score_5 = 2 * possibleMovesScores5[0] # weight = 2
            if depth == 3: 
                Smart_score_3 = 1.5 * possibleMovesScores[0] # weight = 1.5
                Smart_score_5 = 2 * possibleMovesScores5[0]
                del possibleMovesScores[0]
                Smart_score = Smart_score_3 + Smart_score_5

            #print(target_pos, depth)
            # timeout
            if (clock.isTimeoutClose()):
                print('Timeout')
                if len(scores) > 0: #do we have results ?
                    return max(scores.items(), key=operator.itemgetter(1))
                else: #otherwise return big malus
                    return None, -1000

            minimax.nb_nodes_explore+=1 # stat to inform us
            
            new_board = current_board.generate_move(target_pos) # make this move 
            # Change player role for min player - next node is about the other player.
            new_board.is_vampire = not current_board.is_vampire 
            # Compute current leaf score - Recursion 
            result = minimax(new_board, exploredPositions, heuristicHistory, possibleMovesScores,possibleMovesScores5, Smart_score, clock, depth -1, 
                             alpha, beta, not isMax)
            scores[target_pos] = result[1]
            # Alpha - beta def
            alpha = max(result[1], alpha)
            # Pruning condition
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
            result = minimax(new_board, exploredPositions, heuristicHistory,possibleMovesScores,possibleMovesScores5,Smart_score, clock, depth -1, alpha, beta, not isMax)
            scores[target_pos] = result[1]
            # Alpha - beta def
            beta = min(result[1], beta)
            #alpha beta pruning condition
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
        possibleMovesScores = []
        possibleMovesScores5 = [[0]]
        Smart_score = 0 
        new_pos = [minimax(current_board, exploredPositions, heuristicHistory, possibleMovesScores, possibleMovesScores5, Smart_score, clock)[0]]
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
    


def getSmarterHeuristic(board, heuristicHistory, Smart_score): 
    """
    Heuristic function 
    """
    hash = board.hash()
    if (hash in heuristicHistory):
        heuristic = heuristicHistory[hash]
        
    else: 
        score = 0 
        # Store essential information 
        our_position, our_unit_nb = board.getBiggestPosition()
        units_nb = board.getCurrentUnitsNumber()
        total_units_nb = board.getCurrentUnitsNumberSum() 
        our_pos = board.getCurrentPositions()

        humans_pos = np.array(list(board.humansPos.keys()),dtype=(int, int))
        humans_nb = np.array(list(board.humansPos.values()),dtype=int)
        total_humans_nb = np.sum(humans_nb)

        enemy_pos = np.array(board.getOpponentCurrentPositions(),dtype=(int, int))
        enemy_nb = np.array(board.getOpponentUnitsNumber(),dtype=int)
        opponents_unit_nb = board.getOpponentUnitsNumberSum()

        distanceEnemies = [np.max(np.abs(np.subtract(list(enemy), our_position))) for enemy in enemy_pos]
        # distanceHumans = [np.max(np.abs(np.subtract(list(human_loc), our_position)))

        """
        # Consider the case where there is no human left 
        if total_humans_nb == 0: 
            for dist, enemy_unit in zip(distanceEnemies, enemy_nb):
                if (enemy_unit < 1.5 * total_units_nb): score += 10000 / ((dist+1)*(enemy_unit))
                else: 
                    score -= 10 /(dist+1) 
            heuristic = score
            heuristicHistory[hash] = heuristic
            # consider distance of ennemy with our units --> if = 1, bad.

        else: 
        """
        # Consider eatable humans and proximity - does not deal with split yet
        potential_units = total_units_nb 
        for humans_loc, human_unit in zip(humans_pos, humans_nb):
            dist = np.max(np.abs(np.subtract(humans_loc, our_position)))
            if(human_unit > potential_units): p = 0
            elif(total_units_nb >= human_unit): p = 1
            else: p = 2/3

            distEH = min([np.max(np.abs(np.subtract(list(enemy), humans_loc))) for enemy in enemy_pos])
            if ((distEH)/(dist+1) <= 1/4): q= 0.5
            elif (0.9 < (distEH+1)/(dist+1) and (distEH+1)/(dist+1) < 1.2): q = 1.2
            else: q=1

            score += p*q*human_unit/(dist+1)
            potential_units += human_unit
        
        # Consider ennemies 
        for dist, enemy_unit in zip(distanceEnemies, enemy_nb):  
            if(enemy_unit >= 1.5 * total_units_nb): score -= (enemy_unit - total_units_nb)/(dist+1) # avoid 
            elif (total_units_nb > 1.5* enemy_unit): score += (total_units_nb - enemy_unit)/(dist+1) # go towards 
            else: score += 1/(dist+1)  # if no humans left, go attack 
        # consider distance of ennemy with our units --> if = 1, bad. 
                

        # Compute heuristic 
        greedy = 4 # how greedy we want our bot to be, meaning how much does it values the units gained within tree search 
        # score is weighted by 1, Smart_score by 3.5. 
        heuristic = score + Smart_score - greedy * opponents_unit_nb + greedy * total_units_nb 
        heuristicHistory[hash] = heuristic
    return heuristic 



def getHeuristic(board, heuristicHistory, Smart_score):
    
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