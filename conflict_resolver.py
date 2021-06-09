



from feature_vector import FeatureVector
from typing import List

class ConflictResolver:
    def __init__(self):
        self.samples:List[FeatureVector] = []

    def removeDuplicates(self,fvs):  
        uniquePairs = set()
        for index in range(0, len(fvs)):
            uniquePairs.add((fvs[index],fvs[index].counterexampleLabel))
        
        unique = { fv for (fv,l) in uniquePairs}

        return list(unique)


    #res = [x for x in range(len(lst)) if lst[x] == 10]
    def addSamples(self, fvs:List[FeatureVector]):
        
        uniquefvs:List[FeatureVector] = self.removeDuplicates(fvs)
        #TODO: move this to constructor
        if len(self.samples) == 0:
            self.samples.extend(uniquefvs)
            return
        #resolve conflict
        table ={}
        for s in self.samples:
            if  not s in table:
                table[s] = s.counterexampleLabel
            else:
                raise Exception( "conflict already in existing samples -- this cannot happen error!")

        for fv in uniquefvs:
            if fv in table:
                table[fv] = False
            else:
                table[fv] = fv.counterexampleLabel

        for(fv,label) in table:
            fv.counterexampleLabel = label
            self.samples.append(fv)

        pass

    def getSamples():
        pass



