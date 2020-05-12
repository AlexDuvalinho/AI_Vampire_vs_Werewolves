from copy import deepcopy
import numpy as np
import math

class Board:
    def __init__(self, board_h, board_w, initial_board, initial_pos):
        self.humansPos = {} # dict of tuple ((x, y) : nb) indicating positions on board  as key and number of units as value
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

    def getHumansTotalNb(self):
        '''
        Return the total number of humans on the board
        '''
        return np.sum(self.humansPos.values())

    def getAvailableMoves(self, split=False):
        #TODO manage the split : i suggest simplification by only considering 'divide by 2 split' for start
        #TODO add a path to avoid backtracking : no going back on previous positions from tree search
        '''
            return all available positions on board from a current position
        '''
        positions = []

        #TODO change for optim + manage list of positions
        x = self.getBiggestPosition()[0][0] # x of our position (x,y)
        y = self.getBiggestPosition()[0][1] # y of our position (x,y)
    
        for i in range(max(0, x-1),min(self.board_w, x+2)):
            for j in range(max(0, y-1),min(self.board_h, y+2)):
                positions.append([i, j])
        positions.remove([x, y])
        return positions


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


    def PotentialUnits(self, score, position, potential_units ):
        """
        score is the current value of the score. We update this value throughout this function
        Given the potential position considered, consider only humans in the chosen direction
        We sort them by distance and compute the probability to eat them using our potential number of units. 
        The score is a sum dependent on the distance, the number of humans and the proba to eat them  
        """
        original_pos = self.getBiggestPosition()

        q1 = 0.5 
        q2 = 1.2 

        if ((position[0] == original_pos[0][0] - 1) and (position[1] == original_pos[0][1] - 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()): 
                if (human_pos[0] <= original_pos[0][0] and human_pos[1] <= original_pos[0][1]):
                    d = np.max(np.abs(np.subtract(human_pos, position)))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item in dico.values(): 
                if(human_unit > potential_units): p = 0
                else: p = 1
                distEH = min([np.max(np.abs(np.subtract(list(enemy), human_pos))) for enemy in self.getOpponentDict()])
                if ((distEH)/(d+1) <= 1/4): q= q1
                elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                else: q=1
                score += item[1]*p*q/(item[0]+1)
                potential_units += item[1]  
        elif ((position[0] == original_pos[0][0] + 1) and (position[1] == original_pos[0][1] + 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()): 
                if (human_pos[0] >= original_pos[0][0] and human_pos[1] >= original_pos[0][1]):
                    d = np.max(np.abs(np.subtract(human_pos, position)))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item in dico.values(): 
                if(human_unit > potential_units): p = 0
                else: p = 1
                distEH = min([np.max(np.abs(np.subtract(list(enemy), human_pos))) for enemy in self.getOpponentDict()])
                if ((distEH)/(d+1) <= 1/4): q= q1
                elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                else: q=1
                score += item[1]*p*q/(item[0]+1)
                potential_units += item[1]  
        elif ((position[0] == original_pos[0][0] + 1) and (position[1] == original_pos[0][1] - 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()): 
                if (human_pos[0] >= original_pos[0][0] and human_pos[1] <= original_pos[0][1]):
                    d = np.max(np.abs(np.subtract(human_pos, position)))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item in dico.values(): 
                if(human_unit > potential_units): p = 0
                else: p = 1
                distEH = min([np.max(np.abs(np.subtract(list(enemy), human_pos))) for enemy in self.getOpponentDict()])
                if ((distEH)/(d+1) <= 1/4): q= q1
                elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                else: q=1
                score += item[1]*p*q/(item[0]+1)
                potential_units += item[1]  
        elif ((position[0] == original_pos[0][0] - 1) and (position[1] == original_pos[0][1] + 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if (human_pos[0] <= original_pos[0][0] and human_pos[1] >= original_pos[0][1]):
                    d = np.max(np.abs(np.subtract(human_pos, position)))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item in dico.values(): 
                if(human_unit > potential_units): p = 0
                else: p = 1
                distEH = min([np.max(np.abs(np.subtract(list(enemy), human_pos))) for enemy in self.getOpponentDict()])
                if ((distEH)/(d+1) <= 1/4): q= q1
                elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                else: q=1
                score += item[1]*p*q/(item[0]+1)
                potential_units += item[1]  
        elif ((position[0] == original_pos[0][0]) and (position[1] == original_pos[0][1] + 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if ( human_pos[1] -original_pos[0][1] >= np.abs(human_pos[0] - original_pos[0][0]) and human_pos[1] >= original_pos[0][1]):
                    d = np.max(np.abs(np.subtract(human_pos, position)))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item in dico.values(): 
                if(human_unit > potential_units): p = 0
                else: p = 1
                distEH = min([np.max(np.abs(np.subtract(list(enemy), human_pos))) for enemy in self.getOpponentDict()])
                if ((distEH)/(d+1) <= 1/4): q= q1
                elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                else: q=1
                score += item[1]*p*q/(item[0]+1)
                potential_units += item[1]  
        elif ((position[0] == original_pos[0][0]) and (position[1] == original_pos[0][1] - 1)):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if ( original_pos[0][1] - human_pos[1] >= np.abs(human_pos[0] - original_pos[0][0]) and human_pos[1] <= original_pos[0][1]):
                    d = np.max(np.abs(np.subtract(human_pos, position)))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item in dico.values(): 
                if(human_unit > potential_units): p = 0
                else: p = 1
                distEH = min([np.max(np.abs(np.subtract(list(enemy), human_pos))) for enemy in self.getOpponentDict()])
                if ((distEH)/(d+1) <= 1/4): q= q1
                elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                else: q=1
                score += item[1]*p*q/(item[0]+1)
                potential_units += item[1]
        elif ((position[0] == original_pos[0][0]+1) and (position[1] == original_pos[0][1])):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if ( human_pos[0] -original_pos[0][0] >= np.abs(human_pos[1] - original_pos[0][1]) and human_pos[0] >= original_pos[0][0]):
                    d = np.max(np.abs(np.subtract(human_pos, position)))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item in dico.values(): 
                if(human_unit > potential_units): p = 0
                else: p = 1
                distEH = min([np.max(np.abs(np.subtract(list(enemy), human_pos))) for enemy in self.getOpponentDict()])
                if ((distEH)/(d+1) <= 1/4): q= q1
                elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                else: q=1
                score += item[1]*p*q/(item[0]+1)
                potential_units += item[1]
        elif ((position[0] == original_pos[0][0]-1) and (position[1] == original_pos[0][1])):  # not optimised for split 
            dico = {}
            for human_pos, human_unit in zip(self.humansPos, self.humansPos.values()):  
                if ( original_pos[0][0] - human_pos[0] >= np.abs(human_pos[1] - original_pos[0][1]) and human_pos[0] <= original_pos[0][0]):
                    d = np.max(np.abs(np.subtract(human_pos, position)))
                    dico[human_pos] = [d, human_unit]
            dico = dict(sorted(dico.items(), key=lambda kv: kv[1][0], reverse=True))
            for item in dico.values(): 
                if(human_unit > potential_units): p = 0
                else: p = 1
                distEH = min([np.max(np.abs(np.subtract(list(enemy), human_pos))) for enemy in self.getOpponentDict()])
                if ((distEH)/(d+1) <= 1/4): q= q1
                elif (4/5 < (distEH)/(d+1) and (distEH)/(d+1) < 3/2): q = q2
                else: q=1
                score += item[1]*p*q/(item[0]+1)
                potential_units += item[1]

        return score 
 