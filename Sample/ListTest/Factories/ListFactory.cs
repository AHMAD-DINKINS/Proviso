using System;
//using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.Pex.Framework;
using SampleList;

namespace ListTest.Factories
{
    public static class ListFactory
    {
        [PexFactoryMethod(typeof(SampleList.List))]
        public static SampleList.List Create([PexAssumeNotNull]int[] elems){
            PexAssume.IsTrue(elems.Length < 20);
            PexAssume.TrueForAll(0, elems.Length, _i => elems[_i] >= -11 && elems[_i] <= 11);

            List l = new List();
            if(elems.Length ==1)l.value = elems[0];

            for(int i = 1 ; i < elems.Length; i++){
                l.addToEndCorrect(elems[i]);
            }
            return l;

        }

    }
}


