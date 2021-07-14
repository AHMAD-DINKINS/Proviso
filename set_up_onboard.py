import argparse
import json
import os
import pickle
from subprocess import run
from problem import Problem
from runProviso import learnPreconditionForExceptions
import re
from student import Student
import time
import sys
import command_runner
from custom_exceptions import CompilerError
import traceback
from traceback import extract_tb, extract_stack

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
  submissions_proccessed = 0
  skipped = 0
  error = 0
  ran = 0
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
      print("evaluating student: "+f"{student}")
      print("evaluating submission: "+f"{sub['timestamp']}")
      submissions_proccessed += 1
      #TODO json might not be the same for different universities, change this or require same json structure
      result = sub['result']
      code = sub['code']
      problem = sub['question']
      try:
        if problem != 'Sp18_Q11_10' and problem != 'Sp18_Q8_27':
          skipped += 1
          continue
        elif result != "CompilerError":
          set_up(code, class_loc, correct, method, utils)
          if result == "CheckstyleError" or result == "NoScore" or result == "GradingFailure":
            compile_output = command_runner.runCommand("cd ../onboard; mvn compile")
            if not "BUILD SUCCESS" in compile_output:
              raise CompilerError("Submission did not compile with maven")
          output, endtime = run_learner(prob, put, mut)
          #restore(class_loc)
          ran += 1
          counts = submissions_proccessed, skipped, error, ran
          groups = cluster(output, endtime, sub, curr_stu, groups, counts)
      except:
        stack = extract_stack()
        error += 1
        e_type, e_value, e_traceback = sys.exc_info()
        print(e_type)
        print(e_value)
        print(e_traceback)
        tb = traceback.format_exc()
        student = sub['user']
        if not student in exceptions:
          exceptions[sub['user']] = [(sub, tb)]
        else:
          exceptions[sub['user']].append((sub, tb))
        continue
    
  write_exceptions(exceptions)


def run_learner(prob, put, mut):
  startTime = time.time()
  output = learnPreconditionForExceptions(prob, put, mut)
  endtime = time.time() - startTime
  return (output, endtime)


def cluster(output, endtime, sub, curr_stu, groups, counts):
  pre = output[0]
  rounds = output[1]
  groups = group_by_pre(sub, curr_stu, pre, groups, endtime)
  # dumping dictionaries with pickle
  # pickle.dump(groups[0], open("pre_to_stu.p", "wb"))
  pickle.dump(groups[1], open("pre_to_sub.p", "wb"))
  write_result_file(groups[1], rounds, counts)
  return groups


def write_exceptions(exceptions):
  file_name = "exceptions.txt"

  with open(file_name, 'w') as f:
    for student in exceptions:
      for (sub, tb) in exceptions[student]:
        line = f"student: {student} question: {sub['question']} timestamp: {sub['timestamp']} message: {tb}\n"
      f.write(line)

        
def set_up(code, class_loc, correct, method, utils):
  
  with open(correct) as f:
    correct_sol_lines = f.readlines()

  with open(utils) as f:
    utils_lines = f.readlines()

  to_instrument = "".join(correct_sol_lines) + "\n\n" + "".join(utils_lines)

  # in case code does not have a wrapper class
  if "class" not in code:
    with open(class_loc + "PairProgram.java") as f:
      pair_program = "".join(f.readlines())
      end_of_pair_program = pair_program.rindex("}")
      code = pair_program[:end_of_pair_program] + "\n" + code + pair_program[end_of_pair_program]

  end_of_class = code.rindex("}")

  new_code = code[:end_of_class] + "\n" + to_instrument + code[end_of_class]

  method_name = method + "("

  stu_method_name = method_name[:-1] + "Stu("
  if method_name in new_code:
    new_code = new_code.replace(method_name, stu_method_name)

  new_code = new_code.replace("public static int ", "private static int ")

  pattern = r'class ([a-zA-Z]+)'
  # example so we don't overwrite current files
  name_of_class = re.search(pattern, new_code).groups()[0] + ".java"
  name_of_class = os.path.join(class_loc, name_of_class)
  name_of_class = os.path.abspath(name_of_class)
  
  with open(name_of_class, 'w') as f:
    f.write(new_code)

def restore(class_loc):
  with open("./old_pair_program.txt") as f:
    lines = f.readlines()

  with open(class_loc + "PairProgram.java", 'w') as f:
    f.write("".join(lines)) 



#only group code that compiles
def group_by_pre(sub, curr_stu, pre, groups, time):
  # student_dic for analysis
  student_dic, sub_dic = groups if groups else ({},{})
  sub['precondition'] = pre
  sub['learn_time'] = time
  if pre in sub_dic:
    sub_dic[pre].append(sub)
  else:
    sub_dic[pre] = [sub]
  if pre in student_dic:
    student_dic[pre].append(curr_stu)
  else:
    student_dic[pre] = [curr_stu]

  return (student_dic, sub_dic)


def write_result_file(preconditions, rounds, counts):
  total, skipped, error, ran = counts
  file_name = "clusters.txt"
  path = os.path.abspath(file_name)
  with open(path, 'w') as f:
    f.write(f"Total submissions processed: {total}, skipped: {skipped}, error: {error}, ran: {ran}\n")
    for pre in preconditions:
      to_write = f"precondition: {pre}\n"
      submissions = preconditions[pre]
      for sub_idx in range(len(submissions)):
        sub = submissions[sub_idx]
        to_write += f"student: {sub['user']} timestamp: {sub['timestamp']} time: {sub['learn_time']} rounds: {rounds}\n"
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
  javaTestProjectName = 'PairProgram'
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