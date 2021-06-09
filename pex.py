import subprocess
import sys
import re
import os
from os.path import join
import time
import argparse
import collections
import pprint
import csv
import json
import time
import shutil
import io
##from utilityPython import utils
##from benchmarkSet import BenchmarkSet
from teacher import Teacher
from lxml import etree
import command_runner
import time

from feature_vector import FeatureVector
from typing import List

class Pex(Teacher):


    def __init__(self, binary:str, otherArgs:List[str]):
        Teacher.__init__(self, binary, otherArgs)
        self.pexReportFormat = 'Xml'
        self.rn = "XmlReport"  
        self.ro = "rootPre" 
        self.time = 0.0
        self.reportLocation = ""
        self.testsLocation = ""

    def GetExecCommand(self, testDll, testMethod, testNamespace, testType):
        cmd_exec =[self.binary,testDll ,'/membernamefilter:M:'+testMethod+'!', '/methodnamefilter:'+testMethod+'!','/namespacefilter:'+testNamespace +'!', '/typefilter:'+testType+'!']
        cmd_exec.extend(['/ro:'+self.ro, '/rn:'+self.rn,'/rl:'+self.pexReportFormat])
        cmd_exec.extend(self.arguments)
        
        return cmd_exec  

    #consider moving  featureList, preOrpost, kindOfData to  parse report  
    def RunTeacher(self, problem, PUTName, precisFeatureList, preOrPost, kindOfData) -> List[FeatureVector]:
        args = self.GetExecCommand(problem.testDll, PUTName, problem.testNamespace, problem.testClass)
        print((' ').join(args))
        self.time = 0.0
        start_time = time.time()
        pexOutput = command_runner.runCommand((' ').join(args))
        self.time += time.time() - start_time
        print("pexOutput##############")
        print(pexOutput)
        self.reportBaseLocation = problem.testDebugFolder
        self.reportLocation = os.path.join(self.reportBaseLocation, self.ro, self.rn, "report.per")
        self.testsLocation = os.path.join(self.reportBaseLocation, self.ro, self.rn, "tests")

        featVectors: List[FeatureVector] = self.ReadOutput(problem.testDebugFolder, precisFeatureList, preOrPost, kindOfData)
        return featVectors

    def ReadOutput(self, pexReportFolder, precisFeatureList,preOrPost:str, kindOfData)-> List[FeatureVector]:
        #This function should label the field testLabel for a feature vector object
        if "PRE" == preOrPost.upper():
            return self.parseReportForPrecondition(pexReportFolder, precisFeatureList, kindOfData)
        
    
    def parseReportForPrecondition(self, pexReportFolder, precisFeatureList, kindOfData)-> List[FeatureVector]:
        tree = etree.parse(self.reportLocation)
        dataPoints = list()
        featureValues = None
        for test in tree.xpath('//generatedTest'):
            #TODO consider just checing for test.get('status') exception
            # REMIENDER: will need to add more cases for pex internal failures such as the above. We do not want to create feature from these values
            if test.get('status') == 'assumptionviolation':
                continue
            if test.get('status') == 'minimizationrequest':
                print("probably should be re ran with more resources")
                continue
            if test.get('status') == 'pathboundsexceeded':
                print("ideally, this test should be re-ran since path bounds exceeded")
                continue

            singlePoint = ()
            for value in test.xpath('./value'):
                if re.match("^\$.*", value.xpath('./@name')[0]):
                    val = str(value.xpath('string()'))
                    val = self.ReplaceIntMinAndMax(val)
                    val = self.ReplaceTrueAndFalse(val)
                    singlePoint = singlePoint + (val,)
            
            if len(singlePoint) < len(precisFeatureList):
                print("should consider throwing error here")
                continue
            
            if test.get('status') == 'normaltermination':
                #singlePoint = singlePoint + ('True',)
                featureValues = FeatureVector(precisFeatureList, singlePoint, 'True',kindOfData)
            # REMIENDER: will need to add more cases for pex internal failures such as the above. We do not want to create feature from these values
            else:
                #Also for post condition learnig - consider checking that all the failures are of AssertionFailed type. 
                #singlePoint = singlePoint +('False',)
                # check for TermFailure exception
                #print("name of test: "+ str(test.get('name')))
                if test.get('name').find("TermDestruction") != -1:
                    continue
                featureValues = FeatureVector(precisFeatureList, singlePoint, 'False', kindOfData)
            
            assert(featureValues != None)
            dataPoints.append(featureValues)
    
        return dataPoints
 

    
        
    def parseReportPre(self, pexReportFolder):
        pexReportFile = os.path.join(pexReportFolder, self.ro, self.rn, "report.per")
        tree = etree.parse(pexReportFile)
        dataPoints = []
        for test in tree.xpath('//generatedTest'):
            
            singlePoint = []
            for value in test.xpath('./value'):
                if re.match("^\$.*", value.xpath('./@name')[0]):
                    singlePoint.append(str(value.xpath('string()')))

            if test.get('status') == 'normaltermination':
                singlePoint.append('true')

            elif test.get('status') == 'assumptionviolation':
                continue
            elif test.get('status') == 'minimizationrequest':
                continue
            # REMIENDER: will need to add more cases for pex internal failures such as the above. We do not want to create feature from these values
            else:
                singlePoint.append('false')
            # alternatives: test.get('failed') => true / None
            # exceptionState
            # failureText
            dataPoints.append(singlePoint)
        return dataPoints
    
    
    
    
    # refactor this later
    def parseReportPost(self, pexReportFolder):
        if True:  #learner.name == "HoudiniExtended":
            pexReportFile = os.path.join(pexReportFolder, self.ro, self.rn, "report.per")
            tree = etree.parse(pexReportFile)
            dataPoints = set()
            for test in tree.xpath('//generatedTest'):
                # REMIENDER: will need to add more cases for pex internal failures such as the above. We do not want to create feature from these values
                if test.get('status') == 'assumptionviolation' or test.get('status') == 'minimizationrequest':
                    continue
                singlePoint = ()
                for value in test.xpath('./value'):
                    if re.match("^\$.*", value.xpath('./@name')[0]):
                        val = str(value.xpath('string()'))
                        val = self.replaceIntMinAndMax(val)
                        singlePoint = singlePoint + (val,)

                if test.get('status') == 'normaltermination':
                    singlePoint = singlePoint + ('true',)

                else:
                    # Houdini - Only positive points
                    singlePoint = singlePoint +('true',)
                    
                if len(singlePoint) < self.numVariables:
                    continue
                dataPoints.add(singlePoint)
            
            return dataPoints
    
    def ReplaceIntMinAndMax(self, number):
        if number.find("int.MinValue") != -1:
            return "-2147483648"
        elif number.find("int.MaxValue") != -1:
            return "2147483647"
        return number
    
    def ReplaceTrueAndFalse(self, boolean):
        if boolean.upper() == 'TRUE':
            return 'True'
        elif boolean.upper() == 'FALSE':
            return 'False'
        else:
            return boolean