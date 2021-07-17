import subprocess
import sys
import re
import os
import time
import argparse
import collections
import custom_exceptions
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
        self.exceptionsSeen = set()
        
    def runTeacher(self, problem, PUTName, precisFeatureList, preOrPost, kindOfData):
        pass
    
    def parseReportPost(self, pexReportFolder):
        pass

    def getExceptionsSeen(self):
        return self.exceptionsSeen

    # This class needs redesigning because pex must be parsed differently 
    def parseTrace(self, precisFeatureList, example_label):
        dir_of_trace = "../onboard/"
        dataPoints = []
        trace_file_names = os.listdir(dir_of_trace)
        trace_file_names = [file_name for file_name in trace_file_names if example_label in file_name]

        if len(trace_file_names) == 0:
            raise custom_exceptions.TraceMissing(f"No {example_label} trace files found...")

        for file_name in trace_file_names:
            file_name = dir_of_trace + file_name

            with open(file_name) as f:
                lines = f.readlines()

            # find the exit for the values, assuming it is after delcaration exits
            pos_of_first_enter = -1
            for line_idx in range(len(lines)):
                if "ENTER" in lines[line_idx] and not "ppt" in lines[line_idx]:
                    pos_of_first_enter = line_idx
                    break
            if pos_of_first_enter < 0:
                # print("EMPTY TRACE FILE") 
                continue
            new_lines = lines[pos_of_first_enter:]
            points = self.collect_points(new_lines)

            #truncate lines to make easier to iterate over
            vector = self.read_exit(points, precisFeatureList, example_label)
            dataPoints += vector
        self.findExceptions(dir_of_trace + "target/surefire-reports/")
        return dataPoints
    
    def read_exit(self, points, precisFeatureList, example_label):
        test_label=None
        data_points = []
        for key in range(0, len(points), 2):
            if points[key][1].split("\n") == ['']:
                enter = points[key][0].split("\n")
                raise custom_exceptions.NoExitPoint(f"No exit for {enter}...")

            values = []
            # reading exit of wrapper
            read_exit = points[key][1].split("\n")
            # reading enter of inner put
            # read_enter = points[key + 1][0].split("\n")
            for line_idx in range(len(read_exit)):
                if "Old" in read_exit[line_idx]:
                    value = read_exit[line_idx + 1].strip()
                    if value == 'true' or value == 'false':
                        value = value.capitalize()
                    values.append(value)
                if "this.safe" in read_exit[line_idx]:
                    testResult = read_exit[line_idx + 1].strip()
                    testResult = testResult.capitalize()
                    test_label = eval(testResult)
                # elif new_lines[line_idx] == "\n": #TOOD: consider stopping after safe intead of newlinw
                #     break

            vector = FeatureVector(precisFeatureList, values, test_label, example_label)
            data_points.append(vector)
        return data_points
    
    def collect_points(self, lines):
        points = {}
        key = -1
        collecting = False
        point = ""
        for line_idx in range(len(lines)):
            if lines[line_idx] == "\n":
                collecting = False
                if key in points:
                    points[key].append(point)
                else:
                    points[key] = [point]
                point = ""
            elif "ENTER" in lines[line_idx] or "EXIT" in lines[line_idx]:
                collecting = True
            if collecting:
                if "this_invocation_nonce" in lines[line_idx]:
                    key = int(lines[line_idx + 1].strip())
                point += lines[line_idx]

        return points


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
                        self.exceptionsSeen.add(type_of_exception)
                elif error is not None:
                    type_of_exception = error.get('type')
                    if not 'AssumptionViolated' in type_of_exception:
                        self.exceptionsSeen.add(type_of_exception)


