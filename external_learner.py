import time

import reviewData
import z3simplify
from precis_feature import PrecisFeature
from typing import List, Tuple

class  ExternalLearner:
    def __init__(self, name:str, intVars:Tuple[PrecisFeature], boolVars: Tuple[PrecisFeature]):
        self.name = name
        self.dataPoints = set()
        self.boolVariables = boolVars
        self.intVariables = intVars
        self.time  = 0.0
    #TODO: perhaps this method should go to dtlearner.py
    def make_coeff_linear_combination(self, number_of_variables, low, high):
        init_list = [[i] for i in range(low, high + 1)]
        a = init_list
        for i in range(1, number_of_variables):
            a = [x + y for x in a for y in init_list]  # x + y -- concatenation of lists
        return a

    #TODO: maybe require all external learners to setup before learning. So far this method is unnecessary
    def generateInputLanguageFiles(self):
        pass

    #conflictResolver should so this code
    def setDataPoints(self, dataPoints = set()):
        self.dataPoints = dataPoints
        #remove conflicts
        self.dataPoints = reviewData.filterDataPointConflicts(self.dataPoints)



    def runLearner(self):
        pass

    def learn(self, dataPoints, simplify=True):
        self.time = 0.0
        start_time = time.time()

        self.setDataPoints(dataPoints)
        
        self.generateInputFiles()
        result = self.runLearner()
        restoredResults =""
        if result.find("No Solution") == -1:
            if simplify:
                result = z3simplify.simplify(self.intVariables, self.boolVariables, result)

            #print "******  Synthesized Predicate Round Result(Before Restoring): ", result

            #restoredResults = self.restoreVariables(result)
        else:
            restoredResults = result
        
        self.time = time.time() - start_time
        # print "******  Round Result: ", restoredResults
        return restoredResults