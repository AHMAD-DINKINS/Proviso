
from z3.z3 import simplify
from instrumenterCSharp import InstrumenterCSharp
from instrumenterJava import InstrumenterJava
from randoop import Randoop
from problem import Problem
from precis_feature import PrecisFeature
from featurizer import Featurizer
import os
from os import sys, path
from typing import List, Tuple, Type
from pex import Pex
from dtlearner import DTLearner
import shell
from feature_vector import FeatureVector
from conflict_resolver import ConflictResolver
from evosuite import Evosuite
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
        # only add observers used in put
        if "Features" in line:
            tagSeen = True
        if tagSeen:
            # only add observers used in put
            if "Old" in line and not "assumeTrue" in line:
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

def isConsistent(precondition, baseFeatures:Tuple[PrecisFeature], fvs:List[FeatureVector]):
    if precondition == "true" or precondition == "false":
        precondition = precondition.capitalize()
        result = eval(precondition, {},{})
        consistent = all( fv.counterexampleLabel == result for fv in fvs)
        return consistent

    mappings = Featurizer.generateFeatureValueMappingPython(baseFeatures,fvs)

    for mapIdx in range(len(mappings)):
        result = eval(precondition, {}, mappings[mapIdx])
        result = simplify(result)
        if mappings[mapIdx]["label"] and not result:
            return False
        elif not mappings[mapIdx]["label"] and result:
            return False
    return True


def learnPreconditionForExceptions(problem: Problem, putName: str, mut:str):
    featFileName ="typesOM.txt"
    currentStringTree = "true"
    allBaseFeatureVectors =[]

    baseFeatures: Tuple[PrecisFeature] = getFeaturesJava(problem, putName ,featFileName)
    (intBaseFeatures, boolBaseFeatures) = Featurizer.getIntAndBoolFeatures(baseFeatures)

    inst  = InstrumenterJava("mvn compile", "")
    teacherEvo = Evosuite("scripts/run_evosuite.sh", [])
    teacherRand = Randoop("scripts/run_randoop.sh", []) 

    directoryToStoreLearnerFiles = "tempLocation"
    
    learner = DTLearner("dtlearner", "learners/C50exact/c5.0dbg", ['-I 1', '-m 1', '-f' ],directoryToStoreLearnerFiles, \
         intBaseFeatures, boolBaseFeatures)

    learner.generateInputLanguageFile("pre.names")
    #TODO remind to clean up tempLocation after done
    precondition = "true"
    rounds = 1
    resolver = ConflictResolver()
    fvs=[]
    allPreconditions = []
    negFv: List[FeatureVector] = None
    negFvRand: List[FeatureVector] = None
    while True:
        
        if precondition != 'false':
            inst.instrumentPre(problem, precondition, putName)
            inst.remove_assumes(problem.testFileNamePath,putName)#TODO: lines 101-104 can be it's own method in teacher code called get_negative_examples
            inst.remove_assumes(problem.classUnderTestFile, mut)#TODO: will need to implement assume for exception failures in larger programs
            negFv: List[FeatureVector] = teacherEvo.RunTeacher(problem, putName, baseFeatures, "PRE", "NEG" )
            negFvRand: List[FeatureVector] = teacherRand.RunTeacher(problem, putName, baseFeatures, "PRE", "NEG" )
            #negFv: List[FeatureVector] = teacherRand.RunTeacher(problem, putName, baseFeatures, "PRE", "NEG" )
            negFv.extend(negFvRand)

        inst.instrumentPre(problem,"!("+ precondition+")", putName)
        inst.insert_assumes(problem.testFileNamePath,putName)
        inst.insert_assumes(problem.classUnderTestFile, mut)
        posFv: List[FeatureVector] = teacherEvo.RunTeacher(problem, putName, baseFeatures, "PRE", "POS" )
        posFvR: List[FeatureVector] = teacherRand.RunTeacher(problem, putName, baseFeatures, "PRE", "POS" )
        #posFv: List[FeatureVector] = teacherRand.RunTeacher(problem, putName, baseFeatures, "PRE", "POS" )
        posFv.extend(posFvR)

        fvs: List[FeatureVector] =  negFv + posFv
        
        resolver.addSamplesAndResolveConflicts(fvs)
        finalFvs: List[FeatureVector] = resolver.getSamples()

        consistent = isConsistent(precondition,baseFeatures,finalFvs)
        
        if consistent:
            inst.instrumentPre(problem, precondition, putName)
            inst.remove_assumes(problem.testFileNamePath,putName)
            inst.remove_assumes(problem.classUnderTestFile, mut)
            print("found ideal precondition")
            print(precondition) 
            return precondition, rounds
        if rounds == 10:
            print("timeout: Reached limit")
            return precondition, rounds

        latestPre = learner.learn(finalFvs)
            
        
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
    #print(solutionFile)

    # for i in range(0,len(puts)):
    #     learnPreconditionForExceptions(sampleProb, puts[i], muts[i])


    #TODO: Rethink what is required of the Problem class.
    javaClassUnderTestPath = os.path.abspath('../onboard/src/main/java/List.java')
    # end classFile
    javaSolutionFile = ''
    javaTestProjectName = 'ListTest'
    javaTestDebugFolder = ''
    javaTestDll = testDebugFolder + 'ListTest.dll'
    javaTestFileNamePath = os.path.abspath('../onboard/src/main/java/PairProgram.java')
    javaTestFileName = os.path.basename(testFileNamePath)
    javaTestNamespace = ''
    javaTestClass = 'PairProgram'
    javaPuts =['TestStudentSubmission']
    javaMuts=['addToEnd']

    javaSampleProb = Problem(javaSolutionFile, javaTestProjectName, javaTestDebugFolder, javaTestDll, javaTestFileName,javaTestNamespace, javaTestClass, javaTestFileNamePath, javaPuts,javaClassUnderTestPath, javaMuts)
    for i in range(0,len(javaPuts)):
        learnPreconditionForExceptions(javaSampleProb, javaPuts[i], javaMuts[i])

    


if __name__ == '__main__':
    main()