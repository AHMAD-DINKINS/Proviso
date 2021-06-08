using System;
using System.Collections.Generic;
using System.Linq;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Mono.Options;

namespace ObserverTypeExtractor
{
    class Program
    {
        static void Main(string[] args)
        {
            bool showHelp = false;
            string sln = "";
            string testProjectName = "";
            string testFileName = "";
            string PUTName = "";
            string mode = "" ;
            string condition = "";

            OptionSet optionSet = new OptionSet() {
                { "solution=", "Path of solution", v => sln = v },
                { "test-project-name=", "Project name", v => testProjectName = v },
                { "test-file-name=", "Test file name", v => testFileName = v },
                { "PUT-name=", "PUT Name", v => PUTName = v },
                { "mode=", "Pre or Post mode", v =>  mode = v },
                { "condition=", "Condition", v => condition = v },
            };

            try {
                optionSet.Parse(args);
                //Console.WriteLine(sln);
                //Console.WriteLine(testProjectName);
                //Console.WriteLine(testFileName);
                //Console.WriteLine(PUTName);
                //Console.WriteLine(mode);
                //Console.WriteLine(condition);
            }
            catch (OptionException e) {
                Console.Write("Instrumenter.exe ");
                Console.WriteLine(e.Message);
                Console.WriteLine("Try `Instrumenter.exe --help' for more information.");
                return;
            }

            if (showHelp)
            {
                ShowHelpMessage();
                return;
            }

            Debug.Assert(Path.GetExtension(sln).Equals(".sln"), "input args[0] should be a solution file!");
            Utility utility = new Utility(sln, testProjectName, testFileName);
            //Console.WriteLine("here first!");
            if (mode.ToUpper().Equals("PRE"))
                utility.InsertPrecondition(PUTName, condition);
            else if (mode.ToUpper().Equals("POST"))
                utility.PostConditionInsertion(PUTName, condition);
        }

        public static void ShowHelpMessage()
        {
            Console.WriteLine("Instrumenter.exe --solution=<> --project-name=<> --test-file-name=<>" +
                " --PUT-name=<> --post-condition=<>");
        }
    }
}
