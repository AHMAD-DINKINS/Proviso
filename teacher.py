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
import shutil
import io
##from utilityPython import utils
##from benchmarkSet import BenchmarkSet
from lxml import etree
import xml.etree.ElementTree as ET
from feature_vector import FeatureVector

# Teacher is still under design
class Teacher:

    #def __init__(self, testMethod, benchmarkSet, compilerCommand, pexBinary, precondition = "true"):
    #   self.testMethod = testMethod
    #   self.benchmarkSet = benchmarkSet
    #   self.compilerCommand = compilerCommand
    #   self.pexBinary = pexBinary
    #   self.precondition = precondition
    #   self.num_pred = 0
    #   self.done = False
    binary =""
    arguments =[]

    def __init__(self, binary, arguments):
        self.binary = binary
        self.arguments = arguments
        self.time = 0.0
        self.exceptionsSeen = []
        
    def runTeacher(self, problem, PUTName, precisFeatureList, preOrPost, kindOfData):
        pass
    
    def parseReportPost(self, pexReportFolder):
        pass

    def getExceptionsSeen(self):
        return self.exceptionsSeen

    def findExceptions(self, report_loc):
        reports = os.listdir(report_loc)
        reports = [r for r in reports if "TEST" in r]
        for report in reports:
            tree = ET.parse(report_loc + report)
            root = tree.getroot()
            tests = root.findall('testcase')
            for child in tests:
                failure = child.find('failure')
                error = child.find('error')
                if failure is not None:
                    type_of_exception = failure.get('type')
                    if not 'AssumptionViolated' in type_of_exception:
                        self.exceptionsSeen.append(type_of_exception)
                elif error is not None:
                    type_of_exception = error.get('type')
                    if not 'AssumptionViolated' in type_of_exception:
                        self.exceptionsSeen.append(type_of_exception)


