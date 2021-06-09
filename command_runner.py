import subprocess
import sys
import re
import os
import time
import argparse
import collections
import pprint
import csv
import json
import time
import shutil
import io


def runCommand(args):
    try:
        executionOutput = ""
        executionRun = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE,shell=True)
        for line in executionRun.stdout:
            executionOutput += os.linesep + str(line.rstrip())
        executionRun.stdout.close()
        return executionOutput
    except OSError as e:
        print('OSError > ', e.errno)
        print('OSError > ', e.strerror)
        print('OSError > ', e.filename)       
        raise OSError
    except:
        print(e)
        print('Error > ', sys.exc_info()[0])
        raise OSError