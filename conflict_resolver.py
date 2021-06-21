



from feature_vector import FeatureVector
from typing import List

class ConflictResolver:
    def __init__(self):
        self.samples:List[FeatureVector] = []

    def removeDuplicates(self,fvs):  
        uniquePairs = set()
        for index in range(0, len(fvs)):
            uniquePairs.add((fvs[index],fvs[index].counterexampleLabel))
        #TODO just loop over uniquePair and add to list
        unique = { fv for (fv,l) in uniquePairs}

        return list(unique)


    #res = [x for x in range(len(lst)) if lst[x] == 10]
    def addSamplesAndResolveConflicts(self, fvs:List[FeatureVector]):
        
        uniquefvs:List[FeatureVector] = self.removeDuplicates(fvs)
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



