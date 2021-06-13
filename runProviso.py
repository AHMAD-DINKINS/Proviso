
from instrumenterCSharp import InstrumenterCSharp
from instrumenterJava import InstrumenterJava
import problem
from problem import Problem
from precis_feature import PrecisFeature
from featurizer import Featurizer
import os
from os import sys, path
from typing import List, Tuple, Type
from pex import Pex
from dtlearner import DTLearner
# import shell
from feature_vector import FeatureVector
from conflict_resolver import ConflictResolver
import re

def getFeaturesCSharp(p: Problem, putName,featuresFileName):
    # normalize path for windows environment; this must be done even if running on wsl
    p.sln = p.sln.replace("/mnt/c/","c:\\\\")
    p.sln = p.sln.replace("/","\\\\")
    # end of code for path normalization

    p.ExtractObservers(putName, featuresFileName,"Proviso")
    baseFeatures: Tuple[PrecisFeature] = p.ReadObserversFromFile(featuresFileName)
    
    return baseFeatures

def getFeaturesJava(p: Problem, putName,featuresFileName):
    # read test file
    with open(p.testFileNamePath) as f:
        lines = f.readlines()

    declared_observers = {}
    observers_to_write = []
    tagSeen = False
    for line in lines:
        if "Features" in line:
            tagSeen = True
        if tagSeen:
            # only add observers used in put
            if "Old" in line:
                observer = re.search(r"(Old[a-zA-Z]+)", line).groups()[0]
                if observer in declared_observers:
                    observers_to_write.append(observer)
                else:
                    type_info, observer = re.search(r"public ([a-zA-Z]+) (Old[a-zA-Z]+)", line).groups()
                    declared_observers[observer] = type_info
    # write the observers
    with open(featuresFileName, 'w') as f:
        for ob in observers_to_write:
            # truncate ending for "boolean" for observer reader 
            typ = declared_observers[ob].replace("ean", "")
            f.write(ob + " " + typ + "\n")


    baseFeatures: Tuple[PrecisFeature] = p.ReadObserversFromFile(featuresFileName)
    return baseFeatures


def learnPreconditionForExceptions(problem: Problem, putName: str, mut:str):
    featFileName ="typesOM.txt"
    currentStringTree = "true"
    allBaseFeatureVectors =[]

    baseFeatures: Tuple[PrecisFeature] = getFeaturesJava(problem, putName ,featFileName)
    (intBaseFeatures, boolBaseFeatures) = Featurizer.getIntAndBoolFeatures(baseFeatures)

    inst  = InstrumenterJava("cd ../onboard; mvn compile; cd -", "")
    teacher = Pex("pex.exe", ['/nor'])
    directoryToStoreLearnerFiles = "tempLocation"
    
    learner = DTLearner("dtlearner", "learners/C50exact/c5.0dbg", ['-I 1', '-m 1', '-f' ],directoryToStoreLearnerFiles, \
         intBaseFeatures, boolBaseFeatures)

    learner.generateInputLanguageFile("pre.names")
    #TODO remind to clean up tempLocation after done
    precondition = "true"

    
    rounds = 0
    resolver = ConflictResolver()
    fvs=[]
    allPreconditions = []
    while True:
        
        inst.instrumentPre(problem, precondition, putName)
        inst.remove_assumes(problem.testFileNamePath,putName)
        inst.remove_assumes(problem.classUnderTestFile, mut)
        negFv: List[FeatureVector] = teacher.RunTeacher(problem, putName, baseFeatures, "PRE", "NEG" )
        
        inst.instrumentPre(problem,"!("+ precondition+")", putName)
        inst.insert_assumes(problem.testFileNamePath,putName)
        inst.insert_assumes(problem.classUnderTestFile, mut)
        posFv: List[FeatureVector] = teacher.RunTeacher(problem, putName, baseFeatures, "PRE", "POS" )
        
        fvs =  negFv + posFv
        
        resolver.addSamplesAndResolveConflicts(fvs)
        finalFvs: List[FeatureVector] = resolver.getSamples()
        #TODO: check for consistency with precondition and finalFvs, and base features
        latestPre = learner.learn(finalFvs)

        if latestPre in allPreconditions:
            inst.instrumentPre(problem, latestPre, putName)
            inst.remove_assumes(problem.testFileNamePath,putName)
            inst.remove_assumes(problem.classUnderTestFile, mut)
            print("found ideal precondition")
            return latestPre, rounds
        
        allPreconditions.append(latestPre)
        precondition = latestPre
        rounds += 1


def main():
    # classFile is needed for exceptions thrown in code under test and not PUT
    classUnderTestPath = os.path.abspath('Sample/List/List.cs')
    # end classFile
    solutionFile = os.path.abspath('Sample/Sample.sln')
    testProjectName = 'ListTest'
    testDebugFolder = 'Sample/ListTest/bin/Debug/'
    testDll = testDebugFolder + 'ListTest.dll'
    testFileNamePath = os.path.abspath('Sample/ListTest/ListTest.cs')
    testFileName = os.path.basename(testFileNamePath)
    testNamespace = 'SampleList.Test'
    testClass = 'ListTest'
    puts =['PUT_CheckSample']
    muts=['addToEnd']
    sampleProb = Problem(solutionFile, testProjectName, testDebugFolder, testDll, testFileName,testNamespace, testClass, testFileNamePath, puts,classUnderTestPath, muts)
    print(solutionFile)

    # for i in range(0,len(puts)):
    #     learnPreconditionForExceptions(sampleProb, puts[i], muts[i])


    #TODO: Rethink what is required of the Problem class.
    javaClassUnderTestPath = os.path.abspath('../onboard/src/main/java/List.java')
    # end classFile
    javaSolutionFile = ''
    javaTestProjectName = 'ListTest'
    javaTestDebugFolder = ''
    javaTestDll = testDebugFolder + 'ListTest.dll'
    javaTestFileNamePath = os.path.abspath('../onboardtask/src/main/java/AppendPairProgram.java')
    javaTestFileName = os.path.basename(testFileNamePath)
    javaTestNamespace = ''
    javaTestClass = 'AppendPairProgram'
    javaPuts =['TestStudentSubmission']
    javaMuts=['addToEnd']

    javaSampleProb = Problem(javaSolutionFile, javaTestProjectName, javaTestDebugFolder, javaTestDll, javaTestFileName,javaTestNamespace, javaTestClass, javaTestFileNamePath, javaPuts,javaClassUnderTestPath, javaMuts)

    getFeaturesJava(javaSampleProb, javaPuts[0], javaMuts[0])
    exit(0)
    for i in range(0,len(javaPuts)):
        learnPreconditionForExceptions(javaSampleProb, javaPuts[i], javaMuts[i])

    


if __name__ == '__main__':
    main()