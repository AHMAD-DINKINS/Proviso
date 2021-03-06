using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Reflection;
using System.Threading.Tasks;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Symbols;
using Microsoft.CodeAnalysis.CSharp.Syntax;
using Microsoft.CodeAnalysis.Text;
using System.Diagnostics;
using Microsoft.CodeAnalysis.Formatting;
using Microsoft.CodeAnalysis.MSBuild;
using Microsoft.CodeAnalysis.Editing;
using System.Text.RegularExpressions;

namespace ObserverTypeExtractor
{
    class Utility
    {
        MSBuildWorkspace workspace;
        Solution solution;
        DocumentEditor testClassEditor;
        SyntaxTree testClassTree;
        List<MethodDeclarationSyntax> testClassMethods;

        // Note: $var with "Name" doesn't need to be path, but $var without "Name" should be the exact path
        public Utility(string sln, string testProjectName, string testFileName)
        {
            Debug.Assert(File.Exists(sln), "solution file doesn't exist!!!");
            this.workspace = MSBuildWorkspace.Create();
            this.solution = workspace.OpenSolutionAsync(sln).Result;
            //Console.WriteLine(testProjectName);
            Document testClassDocument = FindDocumentByName(testProjectName, testFileName);
            //Environment.Exit(0);
            /**** DEBUG ****/
            Debug.Assert(testClassDocument != null);

            this.testClassEditor = DocumentEditor.CreateAsync(testClassDocument).Result;
            this.testClassTree = testClassDocument.GetSyntaxTreeAsync().Result;
            SyntaxNode testClassRoot = testClassTree.GetRoot();

            this.testClassMethods = testClassRoot.DescendantNodes().OfType<MethodDeclarationSyntax>().ToList();
        }

        public void PostConditionInsertion(string PUTName, string postCondition)
        {
            string AssertionPex = "PexAssert.IsTrue";
            string AssertionNUnit = "Assert.True";
            int targetMethodIdx = FindMethodSyntaxIdxByName(PUTName);
            MethodDeclarationSyntax targetMethod = this.testClassMethods[targetMethodIdx];
            List<StatementSyntax> expressionNodes = targetMethod.DescendantNodes().OfType<StatementSyntax>().ToList();
            foreach (StatementSyntax expr in expressionNodes)
            {
                if (expr.ToString().StartsWith(AssertionNUnit))
                {
                    SyntaxTriviaList trailing = expr.GetTrailingTrivia();
                    SyntaxTriviaList leading = expr.GetLeadingTrivia();
                    StatementSyntax newAsssertStatement = SyntaxFactory.ParseStatement(AssertionNUnit+"(" + postCondition + ");");
                    newAsssertStatement = newAsssertStatement.WithLeadingTrivia(leading).WithTrailingTrivia(trailing);
                    Console.WriteLine(newAsssertStatement.ToString());
                    testClassEditor.ReplaceNode(expr, newAsssertStatement);
                    Document updated = testClassEditor.GetChangedDocument();
                    this.workspace.TryApplyChanges(updated.Project.Solution);
                    break;
                }

                else if (expr.ToString().StartsWith(AssertionPex))
                {
                    SyntaxTriviaList trailing = expr.GetTrailingTrivia();
                    SyntaxTriviaList leading = expr.GetLeadingTrivia();
                    StatementSyntax newAsssertStatement = SyntaxFactory.ParseStatement(AssertionPex + "(" + postCondition + ");");
                    newAsssertStatement = newAsssertStatement.WithLeadingTrivia(leading).WithTrailingTrivia(trailing);
                    Console.WriteLine(newAsssertStatement.ToString());
                    testClassEditor.ReplaceNode(expr, newAsssertStatement);
                    Document updated = testClassEditor.GetChangedDocument();
                    this.workspace.TryApplyChanges(updated.Project.Solution);
                    break;

                }
            }
        }

        public void InsertPrecondition(string PUTName, string precondition)
        {
            string pexAssumption = "PexAssume.IsTrue";
            string AssertionNUnit = "";
            int targetMethodIdx = FindMethodSyntaxIdxByName(PUTName);
            MethodDeclarationSyntax targetMethod = this.testClassMethods[targetMethodIdx];
            List<StatementSyntax> expressionNodes = targetMethod.DescendantNodes().OfType<StatementSyntax>().ToList();
            foreach (StatementSyntax expr in expressionNodes)
            {
                #region multiple assumes
                /* 
                 * if (expr.ToString().StartsWith(AssertionNUnit))
                {
                    SyntaxTriviaList trailing = expr.GetTrailingTrivia();
                    SyntaxTriviaList leading = expr.GetLeadingTrivia();
                    StatementSyntax newAsssertStatement = SyntaxFactory.ParseStatement(AssertionNUnit + "(" + precondition + ");");
                    newAsssertStatement = newAsssertStatement.WithLeadingTrivia(leading).WithTrailingTrivia(trailing);
                    Console.WriteLine(newAsssertStatement.ToString());
                    testClassEditor.ReplaceNode(expr, newAsssertStatement);
                    Document updated = testClassEditor.GetChangedDocument();
                    this.workspace.TryApplyChanges(updated.Project.Solution);
                    break;
                }*/
                #endregion
                if (expr.ToString().StartsWith(pexAssumption))
                {
                    SyntaxTriviaList trailing = expr.GetTrailingTrivia();
                    SyntaxTriviaList leading = expr.GetLeadingTrivia();
                    StatementSyntax newAsssertStatement = SyntaxFactory.ParseStatement(pexAssumption + "(" + precondition + ");");
                    newAsssertStatement = newAsssertStatement.WithLeadingTrivia(leading).WithTrailingTrivia(trailing);
                    Console.WriteLine(newAsssertStatement.ToString());
                    testClassEditor.ReplaceNode(expr, newAsssertStatement);
                    Document updated = testClassEditor.GetChangedDocument();
                    if (this.workspace.TryApplyChanges(updated.Project.Solution))
                        Console.WriteLine("Success");
                   
                    break;

                }
            }
        }



        private int FindMethodSyntaxIdxByName(string methodName)
        {
            for (int i = 0; i < this.testClassMethods.Count; i++)
            {
                if (this.testClassMethods[i].Identifier.ToString().Equals(methodName))
                {
                    return i;
                }
            }
            return -1;
        }

        private Document FindDocumentByName(string projectName, string fileName)
        {
            foreach (Project project in this.solution.Projects)
            {
                if (project.Name.Equals(projectName))
                {
                    foreach (Document document in project.Documents)
                    {
                        if (document.Name.Equals(fileName))
                        {
                            return document;
                        }
                    }
                }
            }
            return null;
        }
    }
}
