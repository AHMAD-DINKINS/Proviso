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

    def parseTrace(self, precisFeatureList, example_label):
        dir_of_trace = "../onboard/"
        dataPoints = []
        trace_file_names = os.listdir(dir_of_trace)
        trace_file_names = [file_name for file_name in trace_file_names if example_label in file_name]
        for file_name in trace_file_names:
            file_name = dir_of_trace + file_name
            test_label = "True" if "PASS" in file_name else "False"
            with open(file_name) as f:
                lines = f.readlines()

            # find the exit for the values, assuming it is after delcaration exits
            pos_of_exit = []
            for line_idx in range(len(lines)):
                if "EXIT" in lines[line_idx] and not "ppt" in lines[line_idx]:
                    pos_of_exit.append(line_idx)
            if len(pos_of_exit) == 0:
                print("COULD NOT FIND EXIT FOR VALUES") 
                exit(0)
            #truncate lines to make easier to iterate over
            for pos in pos_of_exit:
                values = []
                new_lines = lines[pos:]
                for line_idx in range(len(new_lines)):
                    if "Old" in new_lines[line_idx]:
                        value = new_lines[line_idx + 1].strip()
                        if value == 'true' or value == 'false':
                            value = value[0].upper() + value[1:]
                        values.append(value)
                    elif new_lines[line_idx] == "\n":
                        break

                vector = FeatureVector(precisFeatureList, values, test_label, example_label)
                dataPoints.append(vector)

        return dataPoints

    def RunTeacher(self, problem, PUTName, precisFeatureList, preOrPost, kindOfData) -> List[FeatureVector]:
        
        args = self.GetExecCommand(problem.testDll, PUTName, problem.testNamespace, problem.testClass , kindOfData)
        # changeDirOut = command_runner.runCommand("cd ../onboard")
        
        print(args)
        evoOut = command_runner.runCommand(args)
        
        print("evosuite output##############")
        print(evoOut)
        
        featVectors: List[FeatureVector] = self.parseTrace(precisFeatureList, kindOfData) # TODO: Ahmad learn from this guy parseReportForPrecondition in pex.py

        changeDirOut = command_runner.runCommand("cd -")
        print(changeDirOut)
        return featVectors
