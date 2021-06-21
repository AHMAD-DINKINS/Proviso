



from precis_feature import PrecisFeature
from feature_vector import FeatureVector
from typing import List

class ConflictResolver:
    def __init__(self):
        self.samples:List[FeatureVector] = []

    def removeDuplicates(self,fvs:List[FeatureVector]):  
        uniquePairs = set()
        for index in range(0, len(fvs)):
            uniquePairs.add((fvs[index],fvs[index].counterexampleLabel))
        #TODO just loop over uniquePair and add to list
        unique = { fv for (fv,l) in uniquePairs}

        return list(unique)

    def checkNoConflict(self, fvs:List[FeatureVector]):
        table ={}
        for fv in fvs:
            if  not fv in table:
                table[fv] = fv.counterexampleLabel
            else:
                raise Exception( "conflict already in existing samples -- this cannot happen error!")
        return table.items

    #res = [x for x in range(len(lst)) if lst[x] == 10]
    def addSamplesAndResolveConflicts(self, fvs:List[FeatureVector]):
        
        uniquefvs:List[FeatureVector] = self.removeDuplicates(fvs)
        #noConflicfvs = self.checkNoConflict(uniquefvs)

        #TODO: move this to constructor
        if len(self.samples) == 0:
            self.samples.extend(uniquefvs)
            return
        #resolve conflict
        table ={}
        for fv in uniquefvs:
            if  not fv in table:
                table[fv] = fv.counterexampleLabel
            else:
                raise Exception( "conflict already in existing samples -- this cannot happen error!")
        #TODO: no need for table here
        toAdd= []
        
        for (sfv, label) in table.items():
            match = False
            for s in self.samples:
                if s == sfv:
                    match= True
                    if s.counterexampleLabel == True and label:
                        #s.counterexampleLabel = True
                        break
                    elif s.counterexampleLabel == True and not label:
                        print("how rare is this case? ")
                        s.counterexampleLabel = False
                        break
                    elif s.counterexampleLabel == False:
                        #s.counterexampleLabel = False
                        break

            if not match:
                    toAdd.append(sfv)
        
        for ffv in toAdd:
            self.samples.append(ffv)

        # for(fv,label) in table:
        #     fv.counterexampleLabel = label
        #     self.samples.append(fv)

        

    def getSamples(self):
        return list(self.samples)



if __name__ == "__main__":
    intx = PrecisFeature( False, "Oldx", "INT", False)
    inty = PrecisFeature( False, "Oldy", "INT", False)
    feats = [intx, inty]
    
    #Test case 1: conflicting fvs added in two different calls to addSamples
    
    # fv1 =FeatureVector(feats, ['2','1'], False, "NEG")
    # fv2 =FeatureVector(feats, ['2','1'], True, "NEG")
    # fv3 =FeatureVector(feats, ['3','4'], True, "POS")
    # fv4 =FeatureVector(feats, ['3','4'], True, "POS")
    # fv5 =FeatureVector(feats, ['5','6'], True, "POS")

    # r1 = ConflictResolver()
    # r1.addSamplesAndResolveConflicts([fv5,fv2])
    # interFvs = r1.getSamples()
    # assert len(interFvs) == 2 # Adding two different vectors

    # r1.addSamplesAndResolveConflicts([fv1]) #now adding a fv that will cause conflict.
    # interFvs1 = r1.getSamples()
    # assert len(interFvs1) == 2

    #Test case 2: adding conflicting fvs at the same time
    fv1 =FeatureVector(feats, ['2','1'], False, "NEG")
    fv2 =FeatureVector(feats, ['2','1'], True, "NEG")
    fv3 =FeatureVector(feats, ['3','4'], True, "POS")
    fv4 =FeatureVector(feats, ['3','4'], True, "POS")
    fv5 =FeatureVector(feats, ['5','6'], True, "POS")

    r2 = ConflictResolver()
    r2.addSamplesAndResolveConflicts([fv1,fv2])
    interFvs = r2.getSamples()
    assert len(interFvs) == 1 
    pass