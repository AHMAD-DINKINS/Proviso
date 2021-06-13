import io
import os
import re

import command_runner
from problem import Problem


class InstrumenterJava:

    #  Name of compiler executable
    buildExe = ""
    # Name of <tbd> executable
    inserterExe = ""

    def __init__(self, buildExec, inserterExec):
        self.buildExe = buildExec
        self.inserterExe = inserterExec

    #we can move this to the parent class  and only implement the getInstrumentationCommand
    def instrumentPre(self, problem, precondition, PUTname):
        self.instrument(problem, precondition, PUTname,"pre" )
        #if "Success" in instOutput:
        #    print("instrumentation passed")
        
        buildCommand = self.getMsbuildCommand(problem)
        buildOutput = command_runner.runCommand(buildCommand)

    def instrument(self, problem, precondition, PUTname, mode):
        # TODO: make these changes in CSharp instrumenter class
        #instCommand = self.getInstrumentationCommand(problem,precondition, PUTname, mode)
        #instOutput = command_runner.runCommand(instCommand)
        # TODO: write python code to search for second assumeTrue() in TestStudentSubmission and replace with precondition
        #This script assumes that the target assumeTrue will be placed after the observers are initialized within the PUT
        with open(problem.testFileNamePath) as f:
            lines = f.readlines()
        PUTnameSeen = False
        observersSeen = False
        for line_idx in range(len(lines)):
            if PUTname in lines[line_idx]:
                PUTnameSeen = True
            if PUTnameSeen:
                if "Old" in lines[line_idx]:
                    observersSeen = True
                elif observersSeen and "assumeTrue" in lines[line_idx]:
                    oldPreCon = re.search(r'assumeTrue\(([\s\S]*)\);', lines[line_idx]).groups()[0]
                    lines[line_idx] = lines[line_idx].replace(oldPreCon, precondition)
                    break
        
        with open(problem.testFileNamePath, 'w') as f:
            f.write("".join(lines))

    def getInstrumentationCommand(self, problem: Problem, condition: str,PUTName: str, mode:str):
        instruCommand = self.inserterExe + " --solution=" + problem.sln + \
        " --test-project-name=" +problem.projectName+ " --test-file-name=" +problem.testFileName+ " --PUT-name=" +PUTName+" --mode=" +mode+  " --condition="+"\""+condition+"\""
        return instruCommand
    
    def getMsbuildCommand(self,problem):
        buildCommand = self.buildExe+" " + problem.sln+ " /t:rebuild"
        return buildCommand
