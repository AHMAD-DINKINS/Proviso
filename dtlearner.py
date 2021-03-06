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
import os
import itertools
from precis_feature import PrecisFeature
import reviewData
from external_learner import ExternalLearner
import shell
from typing import List, Tuple
import shell
import command_runner
#'-I 1', '-m 1'
class DTLearner(ExternalLearner):
    def __init__(self, name:str, binary:str, parameters:List[str], tempLocation:str, \
    intVariables:Tuple[PrecisFeature], boolVariables:Tuple[PrecisFeature]): 
        
        self.fullPathtoBinary :str = os.path.abspath(binary)
        assert (os.path.exists(self.fullPathtoBinary)), "check that location to binary exists"
        self.fullPathLocation :str = os.path.abspath(tempLocation)
        if not os.path.exists(self.fullPathLocation):
            os.makedirs(self.fullPathLocation)
        
        self.parameters= parameters
        ExternalLearner.__init__(self, name,intVariables,boolVariables )

        

    def generateInputFiles(self, dataPoints:List[FeatureVector]):
        self.writeDataFile(dataPoints)
    
    def writeDataFile(self,dataPoints:List[FeatureVector] ):
        try:
            # change to shell.writeFile
            with open(os.path.join(self.fullPathLocation, 'pre.data'), 'wt') as f_out:
                csv_out = csv.writer(f_out)
                for item in dataPoints:
                    #TODO: this is terrible. either values should be in lower case or upper but need to make better decisions.
                    fvVals = [item.values[idx].lower() for idx in range(len(item.values)) ]
                    tupleFvVals = tuple(fvVals)
                    csv_out.writerow(tupleFvVals+(self.pythonToCSData(item.counterexampleLabel),))
        except Exception as e:
            raise Exception(str(e) + ": " + "error creating data file line 49, dtlearner.py")

    

    

    def generateInputLanguageFile(self, nameOfFile:str):
        fileContents= self.generateFileLinearExpressionsBools()
        try:
            absPath = self.fullPathLocation+'/'+nameOfFile
            with open(absPath, 'wt') as outfile:
                outfile.write(fileContents)

        except Exception as e:
            raise Exception(str(e) + ": " + "error writing files---line 51 dtlearner.py")

    #TODO: needs rewriting for generating prefix terms with -1 * var
    
    def generateFileLinearExpressionsBools(self)-> str:
        coeff_combination = self.make_coeff_linear_combination(len(self.intVariables), -1, 1)
        names_file = 'precondition.'

        for var in self.intVariables:
            names_file += '\n' + var.varName + ':  continuous.'

        # adding boolean observer method features
        for var in self.boolVariables:
            names_file += '\n' + var.varName + ':  true, false.'

        # check equality of integer variables
        if len(self.intVariables) >= 2:
            all_combination = itertools.combinations(self.intVariables, 2)
            for (var1, var2) in all_combination:
                expr = "(" + var1.varName + " = " + var2.varName + ")"
                name_expr = "( = " + var1.varName + " " + var2.varName + " )"
                names_file += '\n' + name_expr + ' := ' + expr + ' .' #needs change

        for coeff in coeff_combination:
            # old way of generating all possible combinations
            expr = ' + '.join(map(lambda x,y: "(" + str(x) + "*" + y.varName + ")", coeff, self.intVariables))
            name_expr = ' ( + ' + ' '.join(map(lambda x,y: "( * " + str(x) + " " + y.varName + " )", coeff, self.intVariables)) + ' )'
            names_file += '\n' + name_expr +  ' := ' + expr + ' .'
        
        
        names_file += '\nprecondition:    true,false.'
        return names_file
    

    # threshold must be passed thtough learnerParameter: -z 80
    def set_c50_args(self):
        result = " ".join([self.fullPathtoBinary ,
                            " ".join(self.parameters)+ " "+ self.fullPathLocation+'/pre' ])
        return  result

    def removeTempFiles(self, files:List[str]):
        try:
            for f in os.listdir(self.fullPathLocation):
                if f in files:
                    os.remove(os.path.join(self.fullPathLocation, f))
        except Exception as e:
            print(str(e))
            raise Exception(str(e))
    
    def runLearner(self):
        #TODO: make param for constructor
        self.removeTempFiles(["pre.tmp","pre.tree", "pre.out", "pre.json"])

        command_runner.runCommand(self.set_c50_args())
        output = self.readResults()
        return output
        
        

    def parse_tree(self, tree):
        try:
            if (tree['children'] is None):
                return '  ' + str(tree['classification']).strip().lower() + ' '

            elif (len(tree['children']) == 2):
                # for parsing bools
                if 'partition' in tree:
                    node =  tree['attribute'] 
                else:
                    node = '( <= ' + tree['attribute'] + ' ' + str(tree['cut']).replace(".0", "") + ' )'
                
                left = self.parse_tree(tree['children'][0]).strip()
                right = self.parse_tree(tree['children'][1]).strip()

                return  '(or   ( and ' +   node  + ' ' + left + ' )  ( and  ( not ' + node + ') ' + right + ' ))'
                # " (" + node + " && (" + left.strip() + ")) || ((!" + node + ") && (" + right.strip() + ")) "


            else:
                shell.printExceptionAndExit(e, "Parsing JSON File")

        except Exception as e:
            shell.printExceptionAndExit(e, "Parsing JSON File")


    def get_pre_from_json(self, path):
        try:
            precondition = "true"
            with open(path) as json_file:
                tree = json.load(json_file)
                precondition = self.parse_tree(tree)

            return precondition
        except Exception as e:
            shell.printExceptionAndExit(e, "Cannot open JSON File")


    def readResults(self):
        return self.get_pre_from_json(self.fullPathLocation + '/pre.json')

        # def writeNamesFile(self):
    #     try:
    #         coeff_combination = self.make_linear_combination(len(self.intVariables), self.intLow, self.intHigh)
    #         names_file = 'precondition.'

    #         for var in self.intVariables:
    #             names_file += '\n' + var.varName + ':  continuous.'

    #         # adding boolean observer method features
    #         for var in self.boolVariables:
    #             names_file += '\n' + var.varName + ':  true, false.'

    #         # check equality of integer variables
    #         if len(self.symbolicIntVariables) >= 2:
    #             all_combination = itertools.combinations(self.intVariables, 2)
    #             for (var1, var2) in all_combination:
    #                 expr = "(" + var1.varName + " = " + var2.varName + ")"
    #                 name_expr = var1.varName + " == " + var2.varName
    #                 names_file += '\n' + name_expr + ' := ' + expr + ' .'

    #         # TODO: for Boolean variables????
    #         # TODO: the learner needs to produce the exact same order of combination ????

    #         for coeff in coeff_combination:
    #             expr = ''
    #             name_expr = ''
    #             join = ''
    #             not_redundant = 0
    #             for i in range(0, len(coeff)):
    #                 not_redundant += coeff[i] * coeff[i]

    #                 if coeff[i] == 0:
    #                     continue
    #                 elif coeff[i] == 1:
    #                     expr = expr + join + self.symbolicIntVariables[i]
    #                     name_expr = name_expr + join + self.symbolicIntVariables[i]
    #                 elif coeff[i] == -1:
    #                     expr = expr + join + '(-' + self.symbolicIntVariables[i] + ')'
    #                     name_expr = name_expr + join + '-' + self.symbolicIntVariables[i]
    #                 else:
    #                     expr = expr + join + '(' + str(coeff[i]) + '*' + self.symbolicIntVariables[i] + ')'
    #                     name_expr = name_expr + join + str(coeff[i]) + '*' + self.symbolicIntVariables[i]

    #                 if not join:
    #                     join = ' + '

    #             if not_redundant >= 2:
    #                 names_file += '\n' + name_expr + ' := ' + expr + ' .'

    #         # old way of generating all possible combinations
    #         # expr = ' + '.join(map(lambda x,y: "(" + str(x) + "*" + str(y) + ")", coeff, IntVariables))
    #         # name_expr = ' + '.join(map(lambda x,y: str(x) + "*" + str(y), coeff, IntVariables))
    #         # names_file += '\n' + name_expr +  ' := ' + expr + ' .'

    #         names_file += '\nprecondition:    true,false.'

    #         shell.writeFile(self.tempLocation, 'pre.names', names_file)

    #     except Exception as e:
    #         shell.printExceptionAndExit(e, "Creating Names File")


    


    # def generateFiles(self):
    #     shell.resetFilesByRegex(self.tempLocation, 'pre\.*')
    #     # self.writeNamesFile()
    #     self.writePrefixNamesFile()
    #     self.writeDataFile()


#test
if __name__ == '__main__':
    learner = DTLearner("dtsolver", "learner/C50exact/c5.0dbg.exe", "", "tempLocation")


    intVariables = ['inta', 'intb', 'intc']
    boolVariables = ['b1', 'b2']
    learner.setVariables(intVariables, boolVariables)


    dataPoints = [[1, 1, 0, "false", "true", "false"],
                [2, 0, 0, "true", "true", "false"],
                [1, 0, 0, "true", "true", "true"],
                [0, 2, 2, "false", "false", "false"],
                #[0, 2147483647, 0, "false", "false", "false"],
                [0, 2, 0, "false", "false", "false"],
                [3, 0, 0, "true", "true", "false"],
                [0, 0, 0, "false", "false", "true"],
                [2, 0, 1, "true", "false", "false"],
                [0, 2, 2, "false", "false", "true"],
                [2, 0, 0, "true", "true", "false"],
                [5, 0, 0, "true", "true", "false"],
                #[0, -2147483647, -2147483648, "false", "false", "false"]
                ]

    # learner.setDataPoints(dataPoints)
    # learner.generateFiles()
    # learner.runLearner()
    # print learner.readResults()

    # print learner.learn(dataPoints)
