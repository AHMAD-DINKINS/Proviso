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
        pass

    def getInstrumentationCommand(self, problem: Problem, condition: str,PUTName: str, mode:str):
        instruCommand = self.inserterExe + " --solution=" + problem.sln + \
        " --test-project-name=" +problem.projectName+ " --test-file-name=" +problem.testFileName+ " --PUT-name=" +PUTName+" --mode=" +mode+  " --condition="+"\""+condition+"\""
        return instruCommand
    
