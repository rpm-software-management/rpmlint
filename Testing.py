import os
import Pkg
import glob

currently_testing = 0
output = []

def isTest():
    return currently_testing

def startTest():
    global currently_testing
    global output
    output = []
    currently_testing = 1

def addOutput(s):
    global output
    output.append(s)

def getOutput():
    global output
    return output

def getTestedPackage(name):
    pkg_path = glob.glob(os.environ['TESTPATH'] + '/' + name + '-*.rpm')[0]
    return Pkg.Pkg(pkg_path, '/tmp')
