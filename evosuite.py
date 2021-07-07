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

class Evosuite(Teacher):
    def __init__(self, binary:str, otherArgs:List[str]):
        Teacher.__init__(self, binary, otherArgs)
        
    def GetExecCommand(self, testDll, testMethod, testNamespace, testType, kindOfData):
        return "cd ../onboard; " + self.binary+ " "+ kindOfData

    def RunTeacher(self, problem, PUTName, precisFeatureList, preOrPost, kindOfData) -> List[FeatureVector]:
        
        args = self.GetExecCommand(problem.testDll, PUTName, problem.testNamespace, problem.testClass , kindOfData)
        # changeDirOut = command_runner.runCommand("cd ../onboard")
        
        print(args)
        evoOut = command_runner.runCommand(args)
        
        #print("evosuite output##############")
        #print(evoOut)
        
        featVectors: List[FeatureVector] = self.parseTrace(precisFeatureList, kindOfData) # TODO: Ahmad learn from this guy parseReportForPrecondition in pex.py

        #changeDirOut = command_runner.runCommand("cd -")
        #print(changeDirOut)
        return featVectors
