using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Microsoft.Pex.Framework;

namespace PexAPIWrapper
{
    public static class AssumePrecondition
    {
        public static void IsTrue(bool cond)
        {
            //try
            //{
                PexAssume.IsTrue(cond);
            //}
            //catch()
        }


    }
}
