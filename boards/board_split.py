from copy import deepcopy
import numpy as np
import math

class Board:
    def __init__(self, board_h, board_w, initial_board, initial_pos):
        self.humansPos = {} # dict of tuple (x, y : nb) indicating positions on board  as key and number of units as value
        self.vampiresPos = {} # list of tuple (x, y : nb) indicating positions on board  as key and number of units as value
        self.werewolvesPos = {} #list of tuple (x, y : nb) indicating positions on board  as key and number of units as value
        self.board_w = board_w
        self.board_h = board_h
        self.is_vampire = None # are we vampire or werewolves
        self.updateBoardInit(initial_board, initial_pos)

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
        #build a new board with current move
        current_pos, current_nb = self.getBiggestPosition()
        
        #generate a new board
        new_board = deepcopy(self)
        
        #update current position
        new_board._simulAction(current_pos[0], current_pos[1], 0)
        
        #update target position
        new_board._simulAction(target_pos[0], target_pos[1], current_nb)
        
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


        if nb_humans > 0: # we need to simulate a fight
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
        inline with getCurrentPositions order
        '''
        if self.is_vampire:
            return list(self.vampiresPos.values())
        return list(self.werewolvesPos.values())
    
    def getCurrentPositions(self):
        '''
        return a list of tuple (x, y) indicating our positions
        (units number is not provided)
        '''
        if self.is_vampire:
            return list(self.vampiresPos.keys())
        return list(self.werewolvesPos.keys())

    def getCurrentDict(self):
        '''
        return a list of tuple (x, y) indicating our positions
        (units number is not provided)
        '''
        if self.is_vampire:
            return (self.vampiresPos)
        return (self.werewolvesPos)
    
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
        inline with getCurrentPositions order
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

    def getAvailableMoves(self, our_position, split=False):
        #TODO manage the split : i suggest simplification by only considering 'divide by 2 split' for start
        #TODO add a path to avoid backtracking : no going back on previous positions from tree search
        '''
            return all available positions on board from a current position
        '''
        positions = []

        #TODO change for optim + manage list of positions
        x = our_position[0]
        y = our_position[1]
    
        for i in range(max(0, x-1),min(self.board_w, x+2)):
            for j in range(max(0, y-1),min(self.board_h, y+2)):
                positions.append([i, j])
        positions.remove([x, y])
        return positions

    def getSmartAvailableMoves(self, size, our_position, split=False):
        '''
            Orders the positions we can move to in a list, where the first one has the highest score 
            It should be explored first during the Tree Search 
        '''
        originalPositions = self.getAvailableMoves(split, our_position)
        size = min(size, len(originalPositions))
        scoreDict = {}
        # evaluate the score for each position
        for position in originalPositions:
            scoreDict[tuple(position)] = self.getAvailableMovesScore(position, self.getCurrentDict(tuple(our_position)))
        # return only the n best positions
        sortedDict = sorted(scoreDict, key = scoreDict.get, reverse = True)
        sortedList = list(map(list, sortedDict))[:size]
        return sortedList

    def getAvailableMovesScore(self, position, unit):
        '''
        compute a score that defines how desirable each position is given how many units you can eat for certain and when (time - dist)
        '''
        eatableOpponents = [k for k in self.humansPos if unit >= self.humansPos[k]] + [k for k in self.getOpponentDict() if unit >= 1.5*self.getOpponentDict()[k]]
        number = [u for u in self.humansPos.values() if unit >= u] + [u for u in self.getOpponentUnitsNumber() if unit >= 1.5 * u]
        distance = [np.max(np.abs(np.subtract(list(enemy), position))) for enemy in eatableOpponents]
        score = np.sum([n/(d+1) for n, d in zip(number, distance)])
        return score

    def getSmarterAvailableMoves(self, size, split = False):
        '''
        attributes a score to each potential move we can make
        This score takes into an up-to-date number of humans as we will move across the map and the ennemies
        deals with the split
        '''
        originalPositions = self.getAvailableMoves(split)
        C = 100  # constant used to emphasize some phenomenons 
        size = min(size, len(originalPositions))
        scoreDict = {}
        for unit in self.getCurrentUnitsNumber():
            for position in originalPositions: # loop through possible positions 
                score = 0

                if(tuple(position) in self.humansPos): # if humans are on our next potential position 
                    if(self.humansPos[tuple(position)] > unit): # don't want to go if they are more than us 
                        score = -100
                    else:
                        score += 10
                
                if (tuple(position) in self.getOpponentDict()):
                    if (self.getOpponentDict().get(tuple(position)) > 1.5 * unit): 
                        score -= 1000  
                    if (self.getOpponentDict().get(tuple(position)) > unit): 
                        score -= 10  
                    else:
                        score += 100
                
                distanceHumans = [np.max(np.abs(np.subtract(list(human), position))) for human in self.humansPos]
                distanceEnemies = [np.max(np.abs(np.subtract(list(enemy), position))) for enemy in self.getOpponentDict()]
                potential_units = unit 
                for dist, human_unit in zip(distanceHumans, self.humansPos.values()):
                    if(human_unit > potential_units): p = 0
                    elif(unit >= human_unit): p = 1
                    else: p = 2/3
                    score += p*human_unit/(dist+1)
                    potential_units += human_unit
                for dist, enemy_unit in zip(distanceEnemies, self.getOpponentDict().values()):
                    if(enemy_unit > unit and enemy_unit < 1.5 * unit): score -= np.abs(enemy_unit - unit)/(dist+1)
                    elif(enemy_unit >= 1.5 * unit): score -= C*np.abs(enemy_unit - unit)/(dist+1)
                    elif (unit > 1.5* enemy_unit): score += C*np.abs(enemy_unit - unit)/(dist+1)
                    else: score += np.abs(enemy_unit - unit)/(dist+1)
                scoreDict[tuple(position)] = score
        sortedDict = sorted(scoreDict, key=scoreDict.get, reverse=True) # sort the dictionnary by score
        #sortedDict = sortedDict[:size]
        sortedList = list(map(list, sortedDict))[:size] # list best potential positions, by order.
        return sortedList
        #sortedDictKeys= dict(sortedDict).keys()
        #return sortedDictKeys
        

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
        return hash_string

def testgetAvailableMoves(self):
    print(self.getAvailableMoves([0, 0], 3, 3))
    print(self.getAvailableMoves([1, 1], 3, 3))
    print(self.getAvailableMoves([2, 2], 3, 3))

def testgetSmartAvailableMoves():
    board_w, board_h = 5, 5
    vampires = {(2, 2) : 5}
    humans = {(1, 1) : 4, (3, 1) : 4, (0, 4) : 1, (4, 4) : 1}
    board = Board(board_w, board_h, [], [])
    board.is_vampire = True
    board.humansPos = humans
    board.vampiresPos = vampires
    board.werewolvesPos = {}
    print(board.getSmartAvailableMoves(4))