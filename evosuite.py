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
        
    def GetExecCommand(self, testDll, testMethod, testNamespace, testType):
        cmd_exec =[self.binary,testDll ,'/membernamefilter:M:'+testMethod+'!', '/methodnamefilter:'+testMethod+'!','/namespacefilter:'+testNamespace +'!', '/typefilter:'+testType+'!']
        cmd_exec.extend(['/ro:'+self.ro, '/rn:'+self.rn,'/rl:'+self.pexReportFormat])
        cmd_exec.extend(self.arguments)
        
        return cmd_exec  

    def RunTeacher(self, problem, PUTName, precisFeatureList, preOrPost, kindOfData) -> List[FeatureVector]:
        args = self.GetExecCommand(problem.testDll, PUTName, problem.testNamespace, problem.testClass)
        argsStr = (' ').join(args)
        print(argsStr)
        pexOutput = command_runner.runCommand((' ').join(args))
        
        print("evosuite output##############")
        print(pexOutput)
        self.reportBaseLocation = problem.testDebugFolder
        self.reportLocation = os.path.join(self.reportBaseLocation, self.ro, self.rn, "report.per")
        self.testsLocation = os.path.join(self.reportBaseLocation, self.ro, self.rn, "tests")

        featVectors: List[FeatureVector] = self.ReadOutput(problem.testDebugFolder, precisFeatureList, preOrPost, kindOfData)
        return featVectors
