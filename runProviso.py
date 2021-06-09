
from instrumenter import Instrumenter
import problem
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

def getFeatures(p: Problem, putName,featuresFileName):
    # normalize path for windows environment; this must be done even if running on wsl
    p.sln = p.sln.replace("/mnt/c/","c:\\\\")
    p.sln = p.sln.replace("/","\\\\")
    # end of code for path normalization

    p.ExtractObservers(putName, featuresFileName,"Proviso")
    baseFeatures: Tuple[PrecisFeature] = p.ReadObserversFromFile(featuresFileName)
    
    return baseFeatures


def learnPreconditionForExceptions(problem: Problem, putName: str, mut:str):
    featFileName ="typesOM.txt"
    currentStringTree = "true"
    allBaseFeatureVectors =[]

    baseFeatures: Tuple[PrecisFeature] = getFeatures(problem, putName ,featFileName)
    (intBaseFeatures, boolBaseFeatures) = Featurizer.getIntAndBoolFeatures(baseFeatures)

    inst  = Instrumenter("MSBuild.exe", "Instrumenter/Instrumenter/bin/Debug/Instrumenter.exe")
    teacher = Pex("pex.exe", ['/nor'])
    directoryToStoreLearnerFiles = "tempLocation"
    
    learner = DTLearner("dtlearner", "learners/C50exact/c5.0dbg", ['-I 1', '-m 1', '-f' ],directoryToStoreLearnerFiles, \
         intBaseFeatures, boolBaseFeatures)

    learner.generateInputLanguageFile("pre.names")
    
    precondition = "OldCount > 5"

    
    rounds = 0
    resolver = ConflictResolver()
    fvs=[]
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
        latestPre = learner.learn(finalFvs)
        precondition = latestPre
        

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
    
    for i in range(0,len(puts)):
        learnPreconditionForExceptions(sampleProb, puts[i], muts[i])



if __name__ == '__main__':
    main()