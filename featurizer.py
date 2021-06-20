from z3 import *

from feature_vector import FeatureVector
from precis_feature import PrecisFeature
from os import sys
from typing import List

import logging


class Featurizer:
    baseFeatures = None
    baseFVs = None
    derivedFeatures = None
    #this should be tuples of base plus derived features
    features = None
    boolFeatures = None
    boolFeaturesIndices = None

    
    
    derivedFVs = None
    #tuple of complete(base + derived) feature vectors
    completeFVs = None
    boolFVs = None
   
    
    # Todo: either derivedFeatures and basefeatures is redundant or features is
    def __init__(self, derivedFeatures, baseFeatures, baseFeatureVectors, features):
        self.baseFVs = baseFeatureVectors
        self.baseFeatures = baseFeatures
        self.derivedFeatures = derivedFeatures
        self.features = features

    @staticmethod
    def getIntAndBoolFeatures(baseFeatures):
        intFeats = ()
        boolFeats = ()
        for f in baseFeatures:
            if str(f.varZ3.sort()).upper() == 'INT':
                intFeats = intFeats + (f,)
            elif str(f.varZ3.sort()).upper() == 'BOOL':
                boolFeats = boolFeats + (f,)
        return intFeats, boolFeats
    
    @staticmethod
    def getBoolAndIntFeatureVectors(intFeats, boolFeats, baseFeatureVectors):
        intFVs =[]
        boolFVs = []
        boolOnlyFV = None
        intOnlyFV = None
        for bf in baseFeatureVectors:
            boolVal = ()
            intVal = ()
            for fVal in bf:
                #print(fVal)
                if is_bool(fVal):
                    boolVal += (str(fVal),)
                elif is_int(fVal):
                    intVal +=(str(fVal),)
            intOnlyFV = FeatureVector(intFeats, intVal, str(bf.testLabel))
            intOnlyFV.ID = bf.ID
            #check for empty boolVal tuple when there are 0 boolean base features
            boolOnlyFV = FeatureVector(boolFeats, boolVal, str(bf.testLabel))
            boolOnlyFV.ID = bf.ID
            #print(boolOnlyFV)
            #print(bf)
            intFVs.append(intOnlyFV)
            boolFVs.append(boolOnlyFV)
        return (intFVs,boolFVs)

    # Inputs:
    #   baseFeatures: list of PrecisFeature containing features provided by user in Parameterized Unit Test(i.e., PUTs)
    #   deriveFeatures: list of PrecisFeature containing feature created from the user provided base features
    #   (i.e., return values of observer methods, and/or parameters of methods and return variables of the method)
    #   baseFeatureVectors: 
    # This funtion extends each FeatureVector object in baseFeatureVector(.i.e., list of FeatureObjects)
    # to contain entries of valuation of derivedFeatures(this shall be boolean features only)
    @staticmethod
    def generateDerivedFeatureVectors( derivedFeatures, baseFeatures, baseFeatureVectors):
        
        #print(derivedFeatures)
        #print(baseFeatureVectors)
        #print ("here")
        #print(baseFeatures)
        pairs = list()
        #consider
        allDerivedFeatureVectors = list()
        for f in baseFeatureVectors:
            #print("feature vec: " +str(f))
            pairs = Featurizer.generateFeatureValueMapping(baseFeatures,f)
            #print(pairs)
            #print(type(pairs))
            derivedTupleValuesZ3 = ()
            for df in derivedFeatures:
                deriveFeatVec = substitute(df.varZ3 , pairs)
                deriveFeatVecValue = simplify(deriveFeatVec)
                derivedTupleValuesZ3 += (deriveFeatVecValue,)

            # Assert: # of derived feature values(i.e. length of derived feature vector(tuple)) should be the same as
            # Assert: # of derived features (.i.e length of list of derived features)
            assert(len(derivedTupleValuesZ3) == len(derivedFeatures))
            derivedFeatureVector = FeatureVector([], [], str(f.testLabel))
            derivedFeatureVector.valuesZ3 = derivedTupleValuesZ3
            derivedFeatureVector.values = tuple(str(i) for i in derivedTupleValuesZ3)
            derivedFeatureVector.ID = f.ID
            allDerivedFeatureVectors.append(derivedFeatureVector)
        return allDerivedFeatureVectors

    @staticmethod
    def generateDerivedFeatureVectorsFromIntFeats( derivedFeatures, intBaseFeatures, baseFeatureVectors):
        
        #print(derivedFeatures)
        #print(baseFeatureVectors)
        #print ("here")
        #print(intBaseFeatures)
        pairs = list()
        #consider
        allDerivedFeatureVectors = list()
        for f in baseFeatureVectors:
            #print("feature vec: " +str(f))
            pairs = Featurizer.generateFeatureValueMapping(intBaseFeatures,f)
            #print(pairs)
            #print(type(pairs))
            derivedTupleValuesZ3 = ()
            for df in derivedFeatures:
                deriveFeatVec = substitute(df.varZ3 , pairs)
                deriveFeatVecValue = simplify(deriveFeatVec)
                derivedTupleValuesZ3 += (deriveFeatVecValue,)

            # Assert: # of derived feature values(i.e. length of derived feature vector(tuple)) should be the same as
            # Assert: # of derived features (.i.e length of list of derived features)
            assert(len(derivedTupleValuesZ3) == len(derivedFeatures))
            derivedFeatureVector = FeatureVector([], [], str(f.testLabel))
            derivedFeatureVector.valuesZ3 = derivedTupleValuesZ3
            derivedFeatureVector.values = tuple(str(i) for i in derivedTupleValuesZ3)
            allDerivedFeatureVectors.append(derivedFeatureVector)    
        #print(allDerivedFeatureVectors)
        return allDerivedFeatureVectors

    @staticmethod
    #checks for duplicates before merging
    def mergeSynthesizedAndGeneratedFeatures(synthFeat, genFeat):
        mergedFeatures = tuple(synthFeat)
        if len(synthFeat) == 0:
            return genFeat
        else:
            for f in genFeat:
                if not (f in synthFeat): # this is a brittle check a != b and b != a returns false
                    mergedFeatures += (f,)
            return mergedFeatures

    @staticmethod
    #checks for duplicates before merging
    def mergeFeatureVectors(baseBoolFvs, derivBoolFvs):
        #Add case if any one of the inputs is empty
        mergedFvs = []
        for i in range(0,len(baseBoolFvs)):
            merged = baseBoolFvs[i]+ derivBoolFvs[i]
            assert(baseBoolFvs[i].ID == derivBoolFvs[i].ID)
            merged.ID = baseBoolFvs[i].ID
            mergedFvs.append(merged)
        return mergedFvs 
            
    @staticmethod
    def generateFeatureValueMappingPython(baseFeatures: List[PrecisFeature], featureVectors:List[FeatureVector]):
        mappings = []
        for fvIdx in range(0, len(featureVectors)):
            entry = {}
            for i in  range(len(baseFeatures)):
                #print("type of featVec", type(featureVector[i]))
                entry[baseFeatures[i].varName] = featureVectors[fvIdx][i]
            entry["label"] = featureVectors[fvIdx].counterexampleLabel
            mappings.append(entry)    
        return mappings

    @staticmethod
    def generateFeatureValueMapping(baseFeatures, featureVector):
        pairs = list()
        # consider removing check for perfomances in cases where the number of feature vectors gets large.
        # number of base features should be the same as the number of entries in feature vector(values of said features)
        #assert(len(featureVector) == len(baseFeatures))
        for i in  range(len(baseFeatures)):
            #print("type of featVec", type(featureVector[i]))
            pair = (baseFeatures[i].varZ3 , featureVector[i])
            pairs.append(pair)
        return pairs


    def GenerateDerivedFeatures(self,intFeat, boolFeat):
        #intFeatures = [f for f in self.baseFeatures if str(f.varZ3.sort())=="Int"]
        #boolFeatures = [f for f in self.baseFeatures if str(f.varZ3.sort())=="Bool"]
        intFeatures = intFeat
        boolFeatures = boolFeat
        negationBaseBoolFeatures =()
        derivedFeatures = ()
        
        

        assert(len(intFeatures) > 0)
        #assert(len(boolFeatures) > 0)
        
        derivedFeatures: Tuple[PrecisFeature] = derivedFeatures + self.CreateInequalities(intFeatures)
        derivedFeatures: Tuple[PrecisFeature] = derivedFeatures + self.CreateInequalitiesWithConstants(intFeatures)
        derivedFeatures: Tuple[PrecisFeature] = derivedFeatures + self.CreateEqualities(intFeatures)
        derivedFeatures: Tuple[PrecisFeature] = derivedFeatures + self.CreateEqualitiesWithConstants(intFeatures) # temp

            #temporarily changed order
        if len(boolFeatures) > 0: # there exist any base bool observer methods
            #pass # do not create negation to reduce space of formulas DT synthesizer has to explore
            negationBaseBoolFeatures: Tuple[PrecisFeature] = self.createNegationBool(boolFeatures)
            #derivedFeatures: Tuple[PrecisFeature] = derivedFeatures + negationBaseBoolFeatures
            derivedFeatures : Tuple[PrecisFeature] = derivedFeatures + negationBaseBoolFeatures
        
        return derivedFeatures
        #return derivedFeatures
        #Todo: call to sygus solvers can be placed here.
    def CreateInequalities(self, intFeatures):
        inequalitiesFeatures = ()
        if len(intFeatures) <= 1:
            return ()
        allCombinations = itertools.combinations(intFeatures,2)
        for (feat1,feat2) in allCombinations:
            #if feat1.isNew == False and feat2.isNew == False:# skip comparison among variables of the pre state only
            #    continue
            lessThanExpr = feat2.varZ3 < feat1.varZ3
            lessThanEqualExpr = feat2.varZ3 <= feat1.varZ3
            lessThanExprReversed = feat1.varZ3 < feat2.varZ3
            lessThanEqualExprReversed = feat1.varZ3 <= feat2.varZ3
            
            lessThanDerived = PrecisFeature(True, str(lessThanExpr), str(lessThanExpr.sort()), None, lessThanExpr)
            lessThanEqualDerived = PrecisFeature(True, str(lessThanEqualExpr), str(lessThanEqualExpr.sort()), None, lessThanEqualExpr)
            lessThanDerivedRev = PrecisFeature(True, str(lessThanExprReversed), str(lessThanExprReversed.sort()), None, lessThanExprReversed)
            lessThanEqualDerivedRev = PrecisFeature(True, str(lessThanEqualExprReversed), str(lessThanEqualExprReversed.sort()), None, lessThanEqualExprReversed)
            
            inequalitiesFeatures += (lessThanDerived,)
            inequalitiesFeatures += (lessThanEqualDerived,)
            inequalitiesFeatures += (lessThanDerivedRev,)
            inequalitiesFeatures += (lessThanEqualDerivedRev,)
            
        return inequalitiesFeatures

    # this method assumes it called with integer features
    def CreateEqualities(self, intFeatures):
        equalitiesFeatures = ()        
        
        if len(intFeatures) <= 1:
            return ()
            #return intFeatures # throw new error
        
        allCombinations = itertools.combinations(intFeatures,2)
        
        for (feat1,feat2) in allCombinations:
            #if feat1.isNew == False and feat2.isNew == False: # skip comparison among variables of the pre state only
            #    continue
            #print (feat1, feat2)
            #removing negation of equalities for now
            notEqualExpr = feat2.varZ3 != feat1.varZ3 
            equalExpr = feat2.varZ3  == feat1.varZ3 
            
            notEqualDerived = PrecisFeature(True, str(notEqualExpr), str(notEqualExpr.sort()), None, notEqualExpr)
            equalDerived = PrecisFeature(True, str(equalExpr), str(equalExpr.sort()), None, equalExpr)
            equalitiesFeatures += (notEqualDerived,)
            equalitiesFeatures += (equalDerived,)
        return equalitiesFeatures

    def CreateEqualitiesWithConstants(self, intFeatures):
        equalitiesWithConstantsFeatures = ()        
        
        if len(intFeatures) == 0:
            return ()
            #return intFeatures # throw new error
        
        for feat1 in intFeatures:
            #print (feat1, feat2)
            equalOneExpr = feat1.varZ3 == IntVal(1)
            equalZeroExpr = feat1.varZ3 == IntVal(0)
            equalNegOneExpr = feat1.varZ3 == IntVal(-1)
            #print(notEqualExpr)
            #print(notEqualExpr.sort())
            #print(type(notEqualExpr))
            equalOneExprDerived = PrecisFeature(True, str(equalOneExpr), str(equalOneExpr.sort()), None, equalOneExpr)
            equalZeroExprDerived = PrecisFeature(True, str(equalZeroExpr), str(equalZeroExpr.sort()), None, equalZeroExpr)
            equalNegOneExprDerived = PrecisFeature(True, str(equalNegOneExpr), str(equalNegOneExpr.sort()), None, equalNegOneExpr)
            equalitiesWithConstantsFeatures += (equalOneExprDerived,)
            equalitiesWithConstantsFeatures += (equalZeroExprDerived,)
            equalitiesWithConstantsFeatures += (equalNegOneExprDerived,)
        return equalitiesWithConstantsFeatures

    def CreateInequalitiesWithConstants(self, intFeatures):
        inequalitiesWithConstantsFeatures = ()        
        
        if len(intFeatures) == 0:
            return ()
            #return intFeatures # throw new error
        
        for feat1 in intFeatures:
            #print (feat1, feat2)
            
            greaterThanNegOneExpr = feat1.varZ3 > IntVal(-1)
            greaterThanEqualNegOneExpr = feat1.varZ3 >= IntVal(-1)
            greaterThanZeroExpr = feat1.varZ3 > IntVal(0)
            greaterThanEqualZeroExpr = feat1.varZ3 >= IntVal(0)
            greaterThanOneExpr = feat1.varZ3 > IntVal(1)
            greaterThanEqualOneExpr = feat1.varZ3 >= IntVal(1)

            greaterThanOneExpr = PrecisFeature(True, str(greaterThanOneExpr), str(greaterThanOneExpr.sort()), None, greaterThanOneExpr)
            greaterThanEqualOneExpr = PrecisFeature(True, str(greaterThanEqualOneExpr), str(greaterThanEqualOneExpr.sort()), None, greaterThanEqualOneExpr)
            greaterThanZeroExpr = PrecisFeature(True, str(greaterThanZeroExpr), str(greaterThanZeroExpr.sort()), None, greaterThanZeroExpr)
            greaterThanEqualZeroExpr = PrecisFeature(True, str(greaterThanEqualZeroExpr), str(greaterThanEqualZeroExpr.sort()), None, greaterThanEqualZeroExpr)
            greaterThanNegOneExpr = PrecisFeature(True, str(greaterThanNegOneExpr), str(greaterThanNegOneExpr.sort()), None, greaterThanNegOneExpr)
            greaterThanEqualNegOneExpr = PrecisFeature(True, str(greaterThanEqualNegOneExpr), str(greaterThanEqualNegOneExpr.sort()), None, greaterThanEqualNegOneExpr)
            
            inequalitiesWithConstantsFeatures += (greaterThanOneExpr,)
            inequalitiesWithConstantsFeatures += (greaterThanEqualOneExpr,)
            inequalitiesWithConstantsFeatures += (greaterThanZeroExpr,)
            inequalitiesWithConstantsFeatures += (greaterThanEqualZeroExpr,)
            inequalitiesWithConstantsFeatures += (greaterThanNegOneExpr,)
            inequalitiesWithConstantsFeatures += (greaterThanEqualNegOneExpr,)
            
        
        return inequalitiesWithConstantsFeatures

    def createNegationBool(self, boolFeatures):
        negBoolFeatures = ()
        for bf in boolFeatures:
            negBoolExpr = Not(bf.varZ3)
            negBoolDerive = PrecisFeature(True, str(negBoolExpr), str(negBoolExpr.sort()), None, negBoolExpr)
            negBoolFeatures += (negBoolDerive,)
        return negBoolFeatures



