import argparse
import json
import os
import pickle
from problem import Problem
from runProviso import learnPreconditionForExceptions
import re
from student import Student
import time
import sys

def parse(submissions):
    # A lot of this will change since I no longer need problems_dict TODO refactor
    # read submissions
    with open(submissions) as f:
        submission_list = json.load(f)
    # sort the submissions by timestamp
    submission_list = sorted(submission_list, key = lambda dic: int(dic['timestamp']))
    
    # A dictionary for hte different problems
    problems_dict = {}
    students_dict = {}

    # fill problems
    for sub in submission_list:
        problem = sub['question']
        if not problem in problems_dict:
            problems_dict[problem] = {}

    # fill students
    for sub in submission_list:
        problem = sub['question']
        student = sub['user']
        if not student in problems_dict[problem]:
            problems_dict[problem][student] = {}
            students_dict[student] = Student(student)

    # fill submissions
    for sub in submission_list:
        problem = sub['question']
        student = sub['user']
        result = sub['result']
        students_dict[student].add_submission(sub)
        if result in problems_dict[problem][student]:
            problems_dict[problem][student][result].append(sub)
        else:
            problems_dict[problem][student][result] = [sub]

    # return the problem directory
    return problems_dict, students_dict


def main(class_loc, correct, method, utils, submissions, prob, put, mut):

  groups = None
  problems, students = parse(submissions)
  #TODO set up needs to init the pair program as well for different problems
  # for problem in problems:
  #   # for testing list
  #   if problem != 'Sp18_Q11_10':
  #     continue
    # might want to sort by time stamp
  exceptions = {}
  for student in students:
    # submissions = problems[problem][student]
    curr_stu = students[student]
    submissions = curr_stu.get_submissions()
    #if len(submissions) >= 4: TODO: not yet know how to filter submission to execute
    #  submissions = submissions[-4:]
    
    # for sub in submissions:
      
      #TODO specific to 125 find different way to skip files that don't compile
      
        # submissions_under_result = submissions[result]
        # submissions_to_run = []
        # length_of_subs = len(submissions_under_result)
        # # not running every submission
        # if length_of_subs >= 1:
        #   submissions_to_run.append(submissions_under_result[0])
        # if length_of_subs >= 2:
        #   submissions_to_run.append(submissions_under_result[-1])
        # if length_of_subs >=3:
        #   submissions_to_run.append(submissions_under_result[length_of_subs // 2])
    for sub in submissions:
      #TODO json might not be the same for different universities, change this or require same json structure
      result = sub['result']
      code = sub['code']
      problem = sub['question']
      if problem != 'Sp18_Q11_10':
        continue
      elif result != "CompilerError" and result != "RuntimeError":
        set_up(code, class_loc, correct, method, utils)
        try:
          pre = ""
          rounds = 0
          startTime = time.time()
          output = learnPreconditionForExceptions(prob, put, mut)
          endtime = time.time() - startTime
          pre = output[0]
          rounds = output[1]
          groups = group_by_pre(sub, curr_stu, pre, groups)
          # dumping dictionaries with pickle
          pickle.dump(groups[0], open("pre_to_stu.p", "wb"))
          pickle.dump(groups[1], open("pre_to_sub.p", "wb"))
          write_result_file(groups[1], endtime)
        except:
          e = sys.exc_info()[0]
          student = sub['user']
          if not student in exceptions:
            exceptions[sub['user']] = [(sub,e)]
          else:
            exceptions[sub['user']].append( (sub, e))
          continue
    
  write_exceptions(exceptions)


def write_exceptions(exceptions):
  file_name = "exceptions.txt"

  with open(file_name, 'w') as f:
    for student in exceptions:
      for (excep, e) in exceptions[student]:
        line = f"student: {student} question: {excep['question']} timestamp: {excep['timestamp']} message: {e}\n"
      f.write(line)

        
def set_up(code, class_loc, correct, method, utils):
  
  with open(correct) as f:
    correct_sol_lines = f.readlines()

  with open(utils) as f:
    utils_lines = f.readlines()

  to_instrument = "".join(correct_sol_lines) + "\n\n" + "".join(utils_lines)

  end_of_class = code.rindex("}")

  new_code = code[:end_of_class] + "\n" + to_instrument + code[end_of_class]

  method_name = method + "("

  new_code = new_code.replace(method_name, method_name[:-1] + "Stu(")

  pattern = r'class ([a-zA-Z]+)'
  # example so we don't overwrite current files
  name_of_class = re.search(pattern, new_code).groups()[0] + ".java"
  name_of_class = os.path.join(class_loc, name_of_class)
  name_of_class = os.path.abspath(name_of_class)
  
  with open(name_of_class, 'w') as f:
    f.write(new_code)


#only group code that compiles
def group_by_pre(sub, curr_stu, pre, groups):
  # student_dic for analysis
  student_dic, sub_dic = groups if groups else ({},{})
  sub['precondition'] = pre
  if pre in sub_dic:
    sub_dic[pre].append(sub)
  else:
    sub_dic[pre] = [sub]
  if pre in student_dic:
    student_dic[pre].append(curr_stu)
  else:
    student_dic[pre] = [curr_stu]

  return (student_dic, sub_dic)


def write_result_file(preconditions, time):
  file_name = "clusters.txt"
  path = os.path.abspath(file_name)
  with open(path, 'w') as f:
    for pre in preconditions:
      to_write = f"precondition: {pre}\n"
      submissions = preconditions[pre]
      for sub_idx in range(len(submissions)):
        sub = submissions[sub_idx]
        to_write += f"student: {sub['user']} {sub['timestamp']} time: {time}\n"
        # FILE:
        # precondition: OldCount <=1
        # student: fasf@illinois.edu Timestamp: 4327892
      f.write(to_write)



if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  
  # will have to change for problems that do not tests methods
  parser.add_argument('--method', metavar="Method", type=str, help='The name of the method used in the problem')
  parser.add_argument('--class-loc', metavar='Location of Class', help='The location to place the class file')
  parser.add_argument('--correct-sol', metavar="Correct Implemenation", type=str, help='The instuctor solution to the problem')
  parser.add_argument('--util', metavar="Utilities", type=str, help="The observer/utility methods to be instrumented into the problem")
  parser.add_argument('--submissions', metavar='Submissions', type=str, help='The json file containing student submissions')

  javaClassUnderTestPath = os.path.abspath('../onboard/src/main/java/List.java')
  # end classFile
  testDebugFolder = 'Sample/ListTest/bin/Debug/'
  testFileNamePath = os.path.abspath('Sample/ListTest/ListTest.cs')
  javaSolutionFile = ''
  javaTestProjectName = 'ListTest'
  javaTestDebugFolder = ''
  javaTestDll = testDebugFolder + 'ListTest.dll'
  javaTestFileNamePath = os.path.abspath('../onboard/src/main/java/PairProgram.java')
  javaTestFileName = os.path.basename(testFileNamePath)
  javaTestNamespace = ''
  javaTestClass = 'PairProgram'
  javaPuts =['TestStudentSubmission']
  javaMuts=['addToEnd']

  args = parser.parse_args()

  class_loc = args.class_loc
  correct = args.correct_sol
  method = args.method
  utils = args.util
  submissions = args.submissions

  javaSampleProb = Problem(javaSolutionFile, javaTestProjectName, javaTestDebugFolder, javaTestDll, javaTestFileName,javaTestNamespace, javaTestClass, javaTestFileNamePath, javaPuts,javaClassUnderTestPath, javaMuts)
  for i in range(0,len(javaPuts)):
      main(class_loc, correct, method, utils, submissions, javaSampleProb, javaPuts[i], javaMuts[i])