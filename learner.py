from feature_vector import FeatureVector
import subprocess
import sys
import re
import os
import time
import argparse
import collections
import pprint
import csv
import json
import time
import shutil
import io
import itertools
import random

# #from utilityPython import utils
# #from benchmarkSet import BenchmarkSet
import shell
import reviewData
import z3simplify


class  Learner:

    def __init__(self, name, binary, parameters,  tempLocation):
        self.name = name
        self.binary = binary
        self.parameters = parameters
        self.tempLocation = tempLocation
        self.dataPoints = []
        self.boolVariables = []
        self.intVariables = []
        self.symbolicBoolVariables = []
        self.symbolicIntVariables = []
        self.time  = 0.0
        
    

    def setVariables(self, intVariables = [], boolVariables = []):
        self.intVariables = intVariables
        self.boolVariables = boolVariables
        self.renameVariables()


    def setDataPoints(self, dataPoints: List[FeatureVector]):
        self.dataPoints = dataPoints
        #remove conflicts
        self.dataPoints = reviewData.filterDataPointConflicts(self.dataPoints)

    # we can get rig of fragile code since Houdini doesnt require re-writing
    def sanitizeNames(self, orinigalName):
        return orinigalName.replace("<=","LEQ").replace(">=","GEQ").replace("==","Equality").replace("=","Eq").replace("!=","NotEquality").replace(".","").replace("(","").replace(")","").replace(" ","").replace("notEq", "NEQ")
    
    
    def renameVariables(self):
        #self.symbolicIntVariables = self.generateSymbolicVariables('Int', len(self.intVariables))
        #self.symbolicBoolVariables  = self.generateSymbolicVariables('Bool', len(self.boolVariables))
        #print str(self.__class__)
        self.symbolicIntVariables = map(lambda x: self.sanitizeNames(x), self.intVariables)
        self.symbolicBoolVariables = map(lambda x: self.sanitizeNames(x), self.boolVariables)

    def restoreVariables(self, precondition):
        
        for i in range(0, len(self.symbolicIntVariables)):
            precondition = precondition.replace(self.symbolicIntVariables[i], self.intVariables[i])

        for i in range(0, len(self.symbolicBoolVariables)):
            precondition = precondition.replace(self.symbolicBoolVariables[i], self.boolVariables[i])
    
        return precondition

     

    def generateFiles(self):
        pass

    def runLearner(self, args):
        pass

    def readResults(self):
        pass

    
    def csToPythonData(self, dataString):
        if dataString == "true":
            return True
        elif dataString == "false":
            return False
        elif dataString.find("true (0x") != -1:
            return True
        elif dataString.find("false (0x") != -1:
            return False
        else:
            #we can only have integers
            return int(dataString)
    
    def pythonToCSData(self, dataValue):
        if dataValue:
            return "true"
        elif not (dataValue):
            return "false"
        else:
            return dataValue
    
    

    def make_linear_combination(self, number_of_variables, low, high):
        init_list = [[i] for i in range(low, high + 1)]
        a = init_list
        for i in range(1, number_of_variables):
            a = [x + y for x in a for y in init_list]  # x + y -- concatenation of lists
        return a


    def learn(self, dataPoints, simplify=True):
        self.time = 0.0
        start_time = time.time()

        self.setDataPoints(dataPoints)
        
        self.generateFiles()
        result = self.runLearner()
        restoredResults =""
        if "True" == result.strip():
            return "true"# in csharp/java, constant "true" is lower case
        if "False" == result.strip():
            return "false"# in csharp/java, constant "true" is lower case
        
        if result.find("No Solution") == -1:
            if simplify:
                result = z3simplify.simplify(self.symbolicIntVariables, self.symbolicBoolVariables, result)

            #print "******  Synthesized Predicate Round Result(Before Restoring): ", result
            restoredResults = self.restoreVariables(result)
        else:
            restoredResults = result
        
        self.time = time.time() - start_time
        # print "******  Round Result: ", restoredResults
        return restoredResults
        
        

# #test
# if __name__ == '__main__':
#     learner = Learner("dtlearner", "c5.0.exe", "-I -m 1 -f ", "../pre", Shell("wsl"))


#     intVariables = ['inta', 'intb', 'intc']
#     boolVariables = ['b1', 'b2']
#     learner.setVariables(intVariables, boolVariables)


#     dataPoints = [[1, 1, 0, "false", "true", "false"],
#                 [2, 0, 0, "true", "true", "false"],
#                 [1, 0, 0, "true", "true", "true"],
#                 [0, 2, 2, "false", "false", "false"],
#                 #[0, 2147483647, 0, "false", "false", "false"],
#                 [0, 2, 0, "false", "false", "false"],
#                 [3, 0, 0, "true", "true", "false"],
#                 [0, 0, 0, "false", "false", "true"],
#                 [2, 0, 1, "true", "false", "false"],
#                 [0, 2, 2, "false", "false", "true"],
#                 [2, 0, 0, "true", "true", "false"],
#                 [5, 0, 0, "true", "true", "false"],
#                 #[0, -2147483647, -2147483648, "false", "false", "false"]
#                 ]

#     learner.setDataPoints(dataPoints)

#     print learner.formatProgram([learner.generateGrammar(), learner.generateConstraints(dataPoints)])





# example interface
# Learners = [
#                 PBE_Learner(name = "pbe learner", binary="../../eu Learner/bin/starexec", param="",  os="linux"),
#                 INV_Learner(name = "inv learner", binary="../../eu Learner/bin/starexec", param="",  os="linux"),
#                 GEN_Learner(name = "general learner", binary="../../eu Learner/bin/starexec", param="",  os="linux"),
#                 PIE_Learner(name = "pie learner", binary="../../eu Learner/bin/starexec", param="",  os="linux"),
#                 DT_Learner(name = "dt exact learner", binary="", parameterized 80% learnerbinary=../../eu Learner/bin/starexec",  param="",  os="linux")
#                 DT_Learner(name = "dt 80pc learner", "exact... ")
#                 DT_Learner(name = "dt 60pc learner learner", )
#             ]
