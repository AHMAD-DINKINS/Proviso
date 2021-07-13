import argparse
import re


def sort_cluster(cluster_file):
  with open(cluster_file) as f:
    lines = f.readlines()

  
  lastest_pre = ""
  results = {}
  for line in lines:
    if "precondition" in line:
      pattern = r'precondition: ?([\(\)a-zA-Z0-9><= _!+-]+)'
      match = re.match(pattern, line)
      lastest_pre = match.group(1)
    elif "student" in line:
      pattern = r'student: ?([a-zA-Z0-9\.@]+) timestamp: ([0-9]+)'
      match = re.match(pattern, line)
      student = match.group(1)
      timestamp = int(match.group(2))
      if student in results:
        results[student].append((timestamp, lastest_pre))
      else:
        results[student] = [(timestamp, lastest_pre)]
  
  

  with open("sorted_clusters.txt", 'w') as f:
    for student in results:
      result_list = results[student]
      to_write = f"""Student: {student}"""
      result_list = sorted(result_list, key = lambda tup: tup[0])
      for idx in range(len(result_list)):
        timestamp, precondition = result_list[idx]
        to_write += f"""
{idx + 1}. timestamp: {timestamp}, precondition: {precondition}\n"""
      f.write(to_write)



if __name__ == "__main__":
  parser = argparse.ArgumentParser()

  parser.add_argument("-c", "--cluster-file", help="The file containing the clusters", type=str)

  args = parser.parse_args()

  cluster_file = args.cluster_file

  sort_cluster(cluster_file)
