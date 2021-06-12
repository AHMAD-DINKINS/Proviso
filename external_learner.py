from feature_vector import FeatureVector
import time

import reviewData
import z3simplify
from precis_feature import PrecisFeature
from typing import List, Tuple

class  ExternalLearner:
    def __init__(self, name:str, intVars:Tuple[PrecisFeature], boolVars: Tuple[PrecisFeature]):
        self.name = name
        self.dataPoints = []
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

    def pythonToCSData(self, dataValue):
        if dataValue:
            return "true"
        elif not (dataValue):
            return "false"
        else:
            return dataValue

        
    def generateInputFiles(self,dataPoints):
        pass


    def runLearner(self):
        pass

    def learn(self, dataPoints, simplify=True):
        self.time = 0.0
        

        #self.setDataPoints(dataPoints)
        result =""

        self.generateInputFiles(dataPoints)
        start_time = time.time()
        result = self.runLearner()
        
        if "true" == result.strip():
            return "true" # in csharp/java, constant "true" is lower case
        if "false" == result.strip():
            return "false" # in csharp/java, constant "false" is lower case
        
        if result.find("No Solution") == -1:
            if simplify:
                result = z3simplify.simplify(self.intVariables, self.boolVariables, result)

        
        self.time = time.time() - start_time
        # print "******  Round Result: ", restoredResults
        return result