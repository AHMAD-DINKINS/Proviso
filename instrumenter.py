import command_runner
import os
import io
import re

from problem import Problem

class Instrumenter:

    #  Name of compiler executable
    buildExe = ""
    # Name of roslyn executable
    inserterExe = ""

    def __init__(self, buildExec, inserterExec):
        self.buildExe = buildExec
        self.inserterExe = inserterExec

    def instrumentPost(self, problem, post,PUTName):
        
        instCommand =self.getInstrumentationCommand(problem, post, PUTName, "post")
        instOutput = command_runner.runCommand(instCommand)
        
        buildCommand = self.getMsbuildCommand(problem)
        buildOutput = command_runner.runCommand(buildCommand)
        
        #print(buildOutput)

    def instrumentPre(self, problem, pre, PUTName):
        instCommand = self.getInstrumentationCommand(problem,pre, PUTName, "pre")
        instOutput = command_runner.runCommand(instCommand)
        #if "Success" in instOutput:
        #    print("instrumentation passed")
        
        buildCommand = self.getMsbuildCommand(problem)
        buildOutput = command_runner.runCommand(buildCommand)

    def getInstrumentationCommand(self, problem: Problem, condition: str,PUTName: str, mode:str):
        instruCommand = self.inserterExe + " --solution=" + problem.sln + \
        " --test-project-name=" +problem.projectName+ " --test-file-name=" +problem.testFileName+ " --PUT-name=" +PUTName+" --mode=" +mode+  " --condition="+"\""+condition+"\""
        return instruCommand

    def getMsbuildCommand(self,problem):
        buildCommand = self.buildExe+" " + problem.sln+ " /t:rebuild"
        return buildCommand

    def instrumentPostString(self, problem, post,PUTName):
        
        instCommand =self.getInstrumentationCommandString(problem, post, PUTName)
        instOutput = command_runner.runCommand(instCommand)
        
        
        buildCommand = self.getMsbuildCommand(problem)
        buildOutput = command_runner.runCommand(buildCommand)

    def getInstrumentationCommandString(self, problem, postcondition,PUTName):
        instruCommand = self.inserterExe + " --solution=" + problem.sln + \
        " --test-project-name=" +problem.projectName+ " --test-file-name=" +problem.testFileName+ " --PUT-name=" +PUTName+ " --post-condition="+"\""+postcondition+"\""
        return instruCommand

    def remove_assumes(self, ClassFilePath, methodUnderTest):
        fullPathCsharpFile = os.path.abspath(ClassFilePath)

        file = list()
        with io.open(fullPathCsharpFile  , 'r',encoding='utf-8-sig') as f:
            file = f.read().splitlines()

        begin = False
        index = -1
        once =True
        nextLine = False
        newContents = []
    
        for line in file:
            if line.find(methodUnderTest) != -1 and once:
                begin = True
                once = False
            #elif begin and line.find("/*Change*/PexAssume.IsTrue(") != -1:
            elif begin and line.find('NotpAssume.IsTrue') != -1 and line.find('//NotpAssume.IsTrue') == -1:
                #print "********before: "+line
                line = line.replace('Notp',"//Notp")
                nextLine = True

            elif nextLine and  line.find('try{PexAssert.IsTrue') != -1 and line.find('//try{PexAssert.IsTrue') == -1:
                line = line.replace('try{PexAssert',"//try{PexAssert")
                nextLine = False
                #print "********commenting: "+line

            elif begin and re.search(r"(?:(?:public)|(?:private)|(?:static)|(?:protected)\s+).*",line,re.DOTALL):# if we see the signature for next method, stop collecting assumes
                begin = False
                        
            newContents.append(line)
                    
            
        with io.open(fullPathCsharpFile, 'w',encoding='utf-8-sig') as fWrite:
            fWrite.write("\n".join(newContents))

    def insert_assumes(self,ClassFilePath, methodUnderTest):
        fullPathCsharpFile= os.path.abspath(ClassFilePath)

        contentsLines = list()
        with io.open(fullPathCsharpFile, 'r',encoding='utf-8-sig') as f:
            contentsLines = f.read().splitlines()
        
        begin = False
        index = -1
        once =True
        nextLine = False
        newContents = []
        
        for line in contentsLines:
            if line.find(methodUnderTest) != -1 and once:
                #this.debug_print("method under test: " + methodUnderTest, False)
                begin = True
                once = False
            elif begin and line.find('//NotpAssume.IsTrue') != -1:
                #print "********before: "+line
                line = line.replace('//',"")
                nextLine = True
            elif nextLine and  line.find('//try{PexAssert.IsTrue') != -1:
                line = line.replace('//',"")
                nextLine = False
                #print "********uncommented: "+line

            elif begin and re.search(r"(?:(?:public)|(?:private)|(?:static)|(?:protected)\s+).*",line,re.DOTALL):# if we see the signature for next method, stop collecting assumes
                begin = False

            newContents.append(line)
        
        
        with io.open(fullPathCsharpFile, 'w',encoding='utf-8-sig') as fWrite:
            fWrite.write("\n".join(newContents))