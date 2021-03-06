using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using SampleList;
using Microsoft.Pex.Framework;
using Microsoft.Pex.Framework.Settings;
using Microsoft.Pex.Framework.Exceptions;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using PexAPIWrapper;

namespace SampleList.Test
{
    [PexClass(typeof(SampleList.List))]
    [TestClass]
    public partial class ListTest
    {
        [PexMethod]
        public void PUT_CheckSample([PexAssumeNotNull]List l, int x)
        {
            
            int OldCount = l.Count();
            PexObserve.ValueForViewing("$input_x", x);
            PexObserve.ValueForViewing("$input_Count", OldCount);

            PexAssume.IsTrue(!(OldCount > 5));
            

            l.addToEnd(x);

            NotpAssume.IsTrue((OldCount + 1) == l.Count());
            PexAssert.IsTrue((OldCount + 1) == l.Count());
        } 
    }
}