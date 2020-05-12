from copy import deepcopy
import numpy as np
import math
import itertools

class Board:
    def __init__(self, board_h, board_w, initial_board, initial_pos):
        self.humansPos = {} # dict of tuple (x, y : nb) indicating positions on board  as key and number of units as value
        self.vampiresPos = {} # list of tuple (x, y : nb) indicating positions on board  as key and number of units as value
        self.werewolvesPos = {} #list of tuple (x, y : nb) indicating positions on board  as key and number of units as value
        self.board_w = board_w
        self.board_h = board_h
        self.is_vampire = None # are we vampire or werewolves
        self.updateBoardInit(initial_board, initial_pos)


    def getSplittingOptions(self, position, max_split, depth = 2):
        """
        Return: all possible positions of splits as well as original available moves 
        Depth: size of the circle around you that you consider (for the split) 
        max_split: maximum number of different units we authorise 
        position: original position of the unit you are considering 
        """
        close_enemy_units = []
        close_enemy_positions = []
        splitting_option_score_full = []
        num_split = len(self.getOurDict()) # number of positions we have 
        x, y = position
        our_unit = self.getOurDict()[tuple(position)] # number of units at this position 

        if(num_split < max_split):  # limit the number of splits
            # get the close by positions
            for i in range(max(0, x - depth), min(self.board_w, x + depth + 1)): # all x-coordinates considered, dist 2 from us
                for j in range(max(0, y - depth), min(self.board_h, y + depth + 1)): # all y-coordinates considered, dist 2 from us
                    # Look at eatable enemies and humans that are present in this area
                    if (i, j) in self.humansPos:  # if we have a human 
                        if self.humansPos[(i, j)] <= our_unit: 
                            close_enemy_positions.append([i, j])
                            close_enemy_units.append(self.humansPos[(i, j)])
                    if (i, j) in self.getOpponentDict(): # if we have an enemy 
                        if self.getOpponentDict()[(i, j)] <= 1.5*our_unit:
                            close_enemy_positions.append([i, j])
                            close_enemy_units.append(self.getOpponentDict()[(i, j)])

            # Generate the splitting options
            target_positions, target_units = [], []
            for i in range(len(close_enemy_units)):
                for j in range(i+1, len(close_enemy_units)): # loop on all units spotted in the area regarded
                    if our_unit - close_enemy_units[i] - close_enemy_units[j] >= 0: # consider next element in the list (cf previous one) 
                        path_pos_i = list(np.add(np.sign(np.add(close_enemy_positions[i], -np.array(position))), position)) # pos where you want to go
                        path_pos_j = list(np.add(np.sign(np.add(close_enemy_positions[j], -np.array(position))), position)) # pos where you want to go
                        if (tuple(path_pos_i) not in self.getCurrentPositions()) and (tuple(path_pos_j) not in self.getCurrentPositions()):
                            if path_pos_i == path_pos_j or close_enemy_units[j] == 0:
                                target_positions.append([path_pos_j]) # append position of pair of units 
                                target_units.append([close_enemy_units[i] + close_enemy_units[j]])  # append their number of units
                            else:
                                target_positions.append([path_pos_i, path_pos_j])
                                target_units.append([close_enemy_units[i], close_enemy_units[j]])

            # even out the remaining units
            for e, u in zip(target_positions, target_units):
                if (np.max(u) - np.min(u)) >= our_unit - np.sum(u): # if we don't need all units for the split
                    u[np.argmin(u)] += our_unit - np.sum(u) # attribute remaining ones to smaller split unit
                else:
                    mini, maxi = np.min(u), np.max(u)
                    u[np.argmin(u)] += maxi - mini  # first add some to min to make both equals
                    u[np.argmin(u)] += int((our_unit - np.sum(u)) / 2)  # then split in 2 what is left 
                    u[np.argmin(u)] += our_unit - np.sum(u)
                if len(e) == 3: # deal with moves obtained without splitting, which have length 3
                    e.append(u[0])
                    e.append(x)
                    e.append(y)
                else:
                    for a, b in zip(e, u): # reformat splitting options 
                        a.append(b)
                        a.append(x)
                        a.append(y)
                splitting_option_score_full.append(tuple(e))

        # adding the non-split options
        for i in range(max(0, x - 1), min(self.board_w, x + 2)):
            for j in range(max(0, y - 1), min(self.board_h, y + 2)):
                if ((i, j) not in self.getCurrentPositions()):
                    splitting_option_score_full.append(tuple([[i, j, our_unit, x, y]]))

        # removing the duplicates
        unique_splitting_options = []
        for element in splitting_option_score_full:
            if(element not in unique_splitting_options): unique_splitting_options.append(element)

        return unique_splitting_options



    def updateBoardInit(self, board, initial_pos):
        for element in board:
            if element[2] != 0: # humans 
                self.humansPos[(element[0], element[1])] = element[2]
            elif element[3] != 0: # vampires
                self.vampiresPos[(element[0], element[1])] = element[3]
                #are we vampires ?
                if (element[0] == initial_pos[0]) and (element[1] == initial_pos[1]):
                    self.is_vampire = True
            elif element[4] != 0: # werewolves
                self.werewolvesPos[(element[0], element[1])] = element[4]
                #are we werewolves ?
                if (element[0] == initial_pos[0]) and (element[1] == initial_pos[1]):
                    self.is_vampire = False
                    
    def getBoard(self):
        return self.humansPos, self.vampiresPos, self.werewolvesPos
                     
                
    def updateBoard(self, updates):
        '''
        update the board with updates provided by server
        '''
        for element in updates:
            if element[2] == 0 : #erase human position if exist
                self.humansPos.pop((element[0], element[1]), -1)
            else: #set the value (insert or update)
                self.humansPos[(element[0], element[1])] = element[2]
                
            if element[3] == 0 : #erase vampires position if exist
                self.vampiresPos.pop((element[0], element[1]), -1)
            else: #set the value (insert or update)
                self.vampiresPos[(element[0], element[1])] = element[3]
                
            if element[4] == 0 : #erase werewolves position if exist
                self.werewolvesPos.pop((element[0], element[1]), -1)
            else: #set the value (insert or update)
                self.werewolvesPos[(element[0], element[1])] = element[4]
        
                
    def generate_move(self, target_pos):
        '''
            generate a new board object from a move from player
            target pos : (tuple (x, y))
            return a new board instance
        '''
        
        current_pos = self.getCurrentPositions()
        
        #generate a new board
        new_board = deepcopy(self)
        
        #erase current positions for our units
        for pos in current_pos:
            new_board._simulAction(pos[0], pos[1], 0)
            
        #generate moves 
        for pos in target_pos:
            new_board._simulAction(pos[0], pos[1], pos[2])
        
        
        return new_board

    
    def _simulAction(self, x, y, nb_units_move):
        '''
        update the board with update(x, y, nb_units_move) provided by simulator
        '''
        
        if nb_units_move == 0: #we remove a position depending of our camp
            if self.is_vampire:
                self.vampiresPos.pop((x, y), -1)
            else:
                self.werewolvesPos.pop((x, y), -1)
            return
                
        
        #Were there humans on the update position ? if yes, get number and remove position
        nb_humans = self.humansPos.pop((x,y), 0)
        
        #Were there enemies on the update position ? if yes, get number and remove position
        if self.is_vampire:
            nb_enemy = self.werewolvesPos.pop((x, y), 0)
        else:
            nb_enemy = self.vampiresPos.pop((x, y), 0)
            
        #are there an unit    
        if self.is_vampire:
            nb_ally = self.vampiresPos.pop((x, y), 0)
        else:
            nb_ally = self.werewolvesPos.pop((x, y), 0)


        if nb_ally > 0 : # we merge units
            if self.is_vampire:
                self.vampiresPos[(x, y)] = nb_units_move + nb_ally
            else :
               self.werewolvesPos[(x, y)] = nb_units_move + nb_ally
            
        elif nb_humans > 0: # we need to simulate a fight
            #calculate probability of win
            if nb_units_move >= nb_humans:
                P = 1
            else: # random battle
                P = nb_units_move / (2 * nb_humans)
            
            #compute the expected outcome
            outcome = math.floor((nb_humans + nb_units_move) * P)
            
            if outcome > 0 : # we win
                #update unit number
                if self.is_vampire:
                    self.vampiresPos[(x, y)] = outcome
                else :
                    self.werewolvesPos[(x, y)] = outcome
            else: #we loose
                self.humansPos[(x, y)] = nb_humans


        elif nb_enemy > 0: # we need to simulate a fight
            #calculate probability of win
            if nb_units_move >= (nb_enemy * 1.5):
                P = 1
            elif nb_units_move * 1.5 <= nb_enemy:
                P = 0
            elif nb_units_move >= nb_enemy :
                P = nb_units_move / nb_enemy - 0.5
            elif nb_units_move <= nb_enemy :
                P = nb_units_move / (2 * nb_enemy)
            
            #compute the expected outcome
            outcome = math.floor(nb_units_move * P)
            
            if outcome > 0 : # we win
                #update unit number
                if self.is_vampire:
                    self.vampiresPos[(x, y)] = outcome
                else :
                    self.werewolvesPos[(x, y)] = outcome
            else: #we loose
                if self.is_vampire:
                    self.werewolvesPos[(x, y)] = nb_enemy
                else :
                   self.vampiresPos[(x, y)] = nb_enemy
                
        else: #simple move
            if self.is_vampire:
                self.vampiresPos[(x, y)] = nb_units_move
            else :
               self.werewolvesPos[(x, y)] = nb_units_move
        
    
    def getCurrentUnitsNumber(self):
        '''
        return a list of number indicating our number of units at each position
        inline with getCurrentpositions order
        '''
        if self.is_vampire:
            return list(self.vampiresPos.values())
        return list(self.werewolvesPos.values())

    def getCurrentUnitsNumberSum(self):
        '''
        return the total number of ennemy units, for all positions 
        '''
        if self.is_vampire:
            return sum(list(self.vampiresPos.values()))
        return sum(list(self.werewolvesPos.values()))
    
    def getCurrentPositions(self):
        '''
        return a list of tuple (x, y) indicating our positions
        (units number is not provided)
        '''
        if self.is_vampire:
            return list(self.vampiresPos.keys())
        return list(self.werewolvesPos.keys())
    
    def getBiggestPosition(self):
        '''
        return our biggest position ((x, y), nb)
        '''
        index = np.argmax(self.getCurrentUnitsNumber())
        
        return self.getCurrentPositions()[index], self.getCurrentUnitsNumber()[index]
    
    def getOpponentUnitsNumberSum(self):
        '''
        return the total number of ennemy units, for all positions 
        '''
        if self.is_vampire:
            return sum(list(self.werewolvesPos.values()))
        return sum(list(self.vampiresPos.values()))
    
    def getOpponentUnitsNumber(self):
        '''
        return a list of values indicating the number of ennemies at each position
        inline with getCurrentpositions order
        '''
        if self.is_vampire:
            return list(self.werewolvesPos.values())
        return list(self.vampiresPos.values())
    
    def getOpponentCurrentPositions(self):
        '''
        return a list of tuple (x, y) indicating all ennemy's positions on the map
        (units number is not provided)
        '''
        if self.is_vampire:
            return list(self.werewolvesPos.keys())
        return list(self.vampiresPos.keys())

    def getOpponentDict(self):
        '''
        Return the number of opponents at each position they occupy
        '''
        if self.is_vampire:
            return self.werewolvesPos
        return self.vampiresPos
    
    def getOurDict(self):
        '''
        Return the number of units at each position we occupy
        '''
        if self.is_vampire:
            return self.vampiresPos
        return self.werewolvesPos
    

    def getAvailableMoves(self, split_max = 1):
        #TODO add a path to avoid backtracking : no going back on previous positions from tree search
        '''
            return all available positions on board from a current position
            split max is the number of maximum split allowed, so far, do not manage more than 2
        '''
        positions = []

        if self.is_vampire:
            current_units = dict(sorted(self.vampiresPos.items(), key=lambda kv: kv[1], reverse=True))
        else:
            current_units = dict(sorted(self.werewolvesPos.items(), key=lambda kv: kv[1], reverse=True))
        
        nb_units = len(current_units)

        #compute the available positions unit by unit
        count = 0
        for (curr_unit, curr_unit_nb) in current_units.items():
            #limit the number of position to process to avoid overload
            if count ==  split_max :
                break
            count += 1
            
            unit_pos = []
            x = curr_unit[0] # x of our position (x,y)
            y = curr_unit[1] # y of our position (x,y)
        
            for i in range(max(0, x-1),min(self.board_w, x+2)):
                for j in range(max(0, y-1),min(self.board_h, y+2)):
                    unit_pos.append([i, j, curr_unit_nb])
            unit_pos.remove([x, y, curr_unit_nb])
            positions.append(unit_pos)
            
        #compute combinatory as split already performed:
        if nb_units > 1 and split_max > 1:
            pos_clean = []
            
            for pos in positions:
                pos_clean.append([item for item in pos if tuple(item[:-1]) 
                                not in self.getCurrentPositions()])
            
            positions = list(itertools.product(*pos_clean))
            return positions
        
        #perform split
        if nb_units == 1 and split_max ==2 and self.getBiggestPosition()[1] > 1 : #we want to split in 2
            xs, ys, nb = zip(*positions[0])
            positions_ = zip(xs, ys)
            
            comb = list(itertools.combinations(positions_, split_max))
            first_half = np.array([nb[0]//2 for x in comb])
            second_half = nb[0] - first_half
            
            first_pos, second_pos = zip(*comb)
            first_pos_x, first_pos_y = zip(*first_pos)
            second_pos_x, second_pos_y = zip(*second_pos)
            
            #return split + non split
            split = [list(a) for a in zip(
                            zip(first_pos_x, first_pos_y, first_half), 
                            zip(second_pos_x, second_pos_y, second_half))] 
            return split + [list([item]) for item in positions[0]]
        
        if nb_units == 1 and split_max ==3 and self.getBiggestPosition()[1] > 3: #we want to split in 3
            xs, ys, nb = zip(*positions[0])
            positions_ = zip(xs, ys)
            
            comb = list(itertools.combinations(positions_, split_max))
            first_third = np.array([nb[0]//3 for x in comb])
            second_third = np.copy(first_third)
            third_third = nb[0] - 2 * second_third
            
            first_pos, second_pos, third_pos = zip(*comb)
            first_pos_x, first_pos_y = zip(*first_pos)
            second_pos_x, second_pos_y = zip(*second_pos)
            third_pos_x, third_pos_y = zip(*third_pos)
            
            #return split + non split
            split = [list(a) for a in zip(
                            zip(first_pos_x, first_pos_y, first_third), 
                            zip(second_pos_x, second_pos_y, second_third),
                            zip(third_pos_x, third_pos_y, third_third))] 
            return split + [list([item]) for item in positions[0]]
        
        
        # we don't want to split or default option
        return [list([item]) for item in positions[0]]


    def hash(self):
        '''
            return the hash for the board
        '''
        hash_string = ''
        for k in self.humansPos:
            hash_string += str(k[0]) + str(k[1]) + str(self.humansPos[k])
        for k in self.vampiresPos:
            hash_string += str(k[0]) + str(k[1]) + str(self.vampiresPos[k])
        for k in self.werewolvesPos:
            hash_string += str(k[0]) + str(k[1]) + str(self.werewolvesPos[k])
        return 
    

    def PotentialUnits(self, x, y, pos_nb, w, z):
        """
        score: current value of the score. We update this value throughout this function
        position: our potential position 
        potential_units: our potential number of units when we reach a human group 
        Given the potential position considered, consider only humans in the chosen direction
        We sort them by distance and compute the probability to eat them using our potential number of units. 
        The score is a sum dependent on the distance, the number of humans and the proba to eat them  
        """

        q1 = 0.5 
        q2 = 1.1 
        potential_units = pos_nb 
        human_score = [0]

        if ((x == w - 1) and (y == z - 1)):  # check in which direction we move 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()): 
                if (human_pos[0] <= w and human_pos[1] <= z):  # only consider humans situated in specific part of the grid
                    d = np.max(np.abs(np.subtract(human_pos, [x,y]))) # compute distance to this human
                    dico[human_pos] = [d, human_unit] # store info
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True)) # sort humans by distance to us
            for item, loc in zip(dico.values(), dico): 
                if(item[1] > potential_units):
                    p = 0
                    q = 1 # does not matter 
                else: 
                    p = 1
                    potential_units += item[1]  
                    distEH = min([np.max(np.abs(np.subtract(list(enemy), loc))) for enemy in self.getOpponentDict()])
                    if ((distEH)/(d+1) <= 1/4): q= q1
                    elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                    else: q=1
                human_score.append(item[1]*p*q /(item[0]+1)) # item[1] is the number of humans, item[0] the distance 

        elif ((x == w + 1) and (y == z + 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()): 
                if (human_pos[0] >= w and human_pos[1] >= z):
                    d = np.max(np.abs(np.subtract(human_pos, [x,y])))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item, loc in zip(dico.values(), dico): 
                if(item[1] > potential_units):
                    p = 0
                    q = 1 # does not matter 
                else: 
                    p = 1
                    potential_units += item[1]  
                    distEH = min([np.max(np.abs(np.subtract(list(enemy), loc))) for enemy in self.getOpponentDict()])
                    if ((distEH)/(d+1) <= 1/4): q= q1
                    elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                    else: q=1
                human_score.append(item[1]*p*q/(item[0]+1)) 

        elif ((x == w + 1) and (y == z - 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()): 
                if (human_pos[0] >= w and human_pos[1] <= z):
                    d = np.max(np.abs(np.subtract(human_pos, [x,y])))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item, loc in zip(dico.values(), dico): 
                if(item[1] > potential_units):
                    p = 0
                    q = 1 # does not matter 
                else: 
                    p = 1
                    potential_units += item[1]  
                    distEH = min([np.max(np.abs(np.subtract(list(enemy), loc))) for enemy in self.getOpponentDict()])
                    if ((distEH)/(d+1) <= 1/4): q= q1
                    elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                    else: q=1
                human_score.append(item[1]*p*q/(item[0]+1)) 

        elif ((x == w - 1) and (y == z + 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if (human_pos[0] <= w and human_pos[1] >= z):
                    d = np.max(np.abs(np.subtract(human_pos, [x,y])))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item, loc in zip(dico.values(), dico): 
                if(item[1] > potential_units):
                    p = 0
                    q = 1 # does not matter 
                else: 
                    p = 1
                    potential_units += item[1]  
                    distEH = min([np.max(np.abs(np.subtract(list(enemy), loc))) for enemy in self.getOpponentDict()])
                    if ((distEH)/(d+1) <= 1/4): q= q1
                    elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                    else: q=1
                human_score.append(item[1]*p*q/(item[0]+1)) 

        elif ((x == w) and (y == z + 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if ( human_pos[1] -z >= np.abs(human_pos[0] - w) and human_pos[1] >= z):
                    d = np.max(np.abs(np.subtract(human_pos, [x,y])))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item, loc in zip(dico.values(), dico): 
                if(item[1] > potential_units):
                    p = 0
                    q = 1 # does not matter 
                else: 
                    p = 1
                    potential_units += item[1]  
                    distEH = min([np.max(np.abs(np.subtract(list(enemy), loc))) for enemy in self.getOpponentDict()])
                    if ((distEH)/(d+1) <= 1/4): q= q1
                    elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                    else: q=1
                human_score.append(item[1]*p*q/(item[0]+1)) 

        elif ((x == w) and (y == z - 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if ( z - human_pos[1] >= np.abs(human_pos[0] - w) and human_pos[1] <= z):
                    d = np.max(np.abs(np.subtract(human_pos, [x,y])))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item, loc in zip(dico.values(), dico): 
                if(item[1] > potential_units):
                    p = 0
                    q = 1 # does not matter 
                else: 
                    p = 1
                    potential_units += item[1]  
                    distEH = min([np.max(np.abs(np.subtract(list(enemy), loc))) for enemy in self.getOpponentDict()])
                    if ((distEH)/(d+1) <= 1/4): q= q1
                    elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                    else: q=1
                human_score.append(item[1]*p*q/(item[0]+1)) 

        elif ((x == w+1) and (y == z)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if ( human_pos[0] -w >= np.abs(human_pos[1] - z) and human_pos[0] >= w):
                    d = np.max(np.abs(np.subtract(human_pos, [x,y])))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item, loc in zip(dico.values(), dico): 
                if(item[1] > potential_units):
                    p = 0
                    q = 1 # does not matter 
                else: 
                    p = 1
                    potential_units += item[1]  
                    distEH = min([np.max(np.abs(np.subtract(list(enemy), loc))) for enemy in self.getOpponentDict()])
                    if ((distEH)/(d+1) <= 1/4): q= q1
                    elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                    else: q=1
                human_score.append(item[1]*p*q/(item[0]+1))  

        elif ((x == w-1) and (y == z)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if ( w - human_pos[0] >= np.abs(human_pos[1] - z) and human_pos[0] <= w):
                    d = np.max(np.abs(np.subtract(human_pos, [x,y])))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item, loc in zip(dico.values(), dico): 
                if(item[1] > potential_units):
                    p = 0
                    q = 1 # does not matter 
                else: 
                    p = 1
                    potential_units += item[1]  
                    distEH = min([np.max(np.abs(np.subtract(list(enemy), loc))) for enemy in self.getOpponentDict()])
                    if ((distEH)/(d+1) <= 1/4): q= q1
                    elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                    else: q=1
                human_score.append(item[1]*p*q/(item[0]+1)) 

        return human_score 


def testgetAvailableMoves_1():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 14, (3, 3) : 18}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {}
    print(board.getAvailableMoves(1))
    print(len(board.getAvailableMoves(1)))

def testgetAvailableMoves_2():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 14, (3, 3) : 18, (4, 3) : 11}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {}
    print(board.getAvailableMoves(2))
    print(len(board.getAvailableMoves(2)))
    
def testgetAvailableMoves_3():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 14}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {}
    print(board.getAvailableMoves(2))
    print(len(board.getAvailableMoves(2)))
    
def testgetAvailableMoves_4():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 14}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {}
    print(board.getAvailableMoves(3))
    print(len(board.getAvailableMoves(3)))
    
def testgetAvailableMoves_5():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 1}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {}
    print(board.getAvailableMoves(2))
    print(len(board.getAvailableMoves(2)))
    
def testgenerate_move():
    board_w, board_h = 5, 5
    vampires = {(2, 1) : 11}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {(1, 0) : 15}
    print(board.generate_move([[1, 0, 11]]).getBoard())
    
def testgenerate_move_merger():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 14, (3, 3) : 18}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {}
    print(board.generate_move([[2, 3, 14], [2, 3, 18]]).getBoard())

def testgetSplittingOptions(pos, num):
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 8, (4, 4) : 1}
    humans = {(0, 0) : 3, (3, 0) : 3, (0, 4) : 3, (1, 4) : 3}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {}
    print(board.getSplittingOptions(pos, num))
