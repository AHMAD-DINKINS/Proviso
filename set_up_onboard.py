import argparse
import json
import os
import re
from student import Student


def parse(submissions):
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


def main(class_loc, correct, method, utils, submissions):

  groups = None
  problems, students = parse(submissions)
  #TODO set up needs to init the pair program as well for different problems
  # for problem in problems:
  #   # for testing list
  #   if problem != 'Sp18_Q11_10':
  #     continue
    # might want to sort by time stamp
  for student in students:
    # submissions = problems[problem][student]
    curr_stu = students[student]
    submissions = curr_stu.get_submissions()
    if len(submissions) >= 4:
      submissions = submissions[-4:]
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
      elif result != "CompileError" and result != "RuntimeError":
        set_up(code, class_loc, correct, method, utils)
        #TODO for testing, replace with call to learner
        pre = "false"
        groups = group_by_pre(sub, curr_stu, pre, groups)

        create_dir(groups[1])

        
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


def create_dir(preconditions):
  for pre in preconditions:
    for sub_idx in range(len(preconditions[pre])):
      # problem = sub['question']
      # write_files(problem, student, result, problems[problem][student][result])
      write_files(pre, preconditions[pre][sub_idx], sub_idx)


def write_files(pre, sub, idx):
  sub_str = json.dumps(sub)
  sub_path = 'sub' + str(idx) + ".json"

  path = os.path.join('preconditions', pre, sub_path)
  basedir = os.path.dirname(path)

  if not os.path.exists(basedir):
      os.makedirs(basedir)
  
  with open(path, 'w') as f:
    f.write(sub_str)


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  
  # will have to change for problems that do not tests methods
  parser.add_argument('--method', metavar="Method", type=str, help='The name of the method used in the problem')
  parser.add_argument('--class-loc', metavar='Location of Class', help='The location to place the class file')
  parser.add_argument('--correct-sol', metavar="Correct Implemenation", type=str, help='The instuctor solution to the problem')
  parser.add_argument('--util', metavar="Utilities", type=str, help="The observer/utility methods to be instrumented into the problem")
  parser.add_argument('--submissions', metavar='Submissions', type=str, help='The json file containing student submissions')

  args = parser.parse_args()

  class_loc = args.class_loc
  correct = args.correct_sol
  method = args.method
  utils = args.util
  submissions = args.submissions

  main(class_loc, correct, method, utils, submissions)