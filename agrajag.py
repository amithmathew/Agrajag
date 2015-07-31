#
# Script              : Agrajag - Autosys JIL to Graph Translator.
# Pre-requisites      : datetime, argparse, pprint, re, graphviz, functools, subprocess
# Output              : 
# Assumptions         : No OR conditions allowed.
# Author              : Amith Mathew
# Version             : 0.1
# License             : GPL3 - Copyright 2015, Amith Mathew
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
# TODO - Lots of cleanup and refactoring needed - but works as a PoC!


# Algorithm
# 1. Parse the JIL file and generate a list of dictionaries with boxes and jobs.
#       This is similar to version 0.1
# 2. Iterate through the jobs in each box and build a list of nodes + edges.
#       2a. When encountering complex conditions, convert into extra nodes and edges as required.
# 3. Call dot to convert the .dot file into jpg.


import datetime
import argparse
#import re
from subprocess import check_call

# Script Version
VERSION = '2.0.0'

# Generate datetime
tstamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# AND or OR box iterator
nodeIter = 1


# Command-line argument parsing
parser = argparse.ArgumentParser(description='Agrajag - Autosys JIL to Graph Translator.', version=VERSION)
parser.add_argument(	'JILFile', 
						metavar='in-file', 
						type=argparse.FileType('rt'),
						help='The JIL .txt file'
				)
args = parser.parse_args()


# Function shamelessly copied from StackOverflow.
def flatten(container):
    for i in container:
        if isinstance(i, list) or isinstance(i, tuple):
            for j in flatten(i):
                yield j
        else:
            yield i


def buildPrefixExpression(condition):
    mod_cond_str = condition.replace(' and ', '&').replace(' or ', '|')
    mod_cond_str = mod_cond_str.replace('(s(', '( s(').replace('(f(', '( f(').replace('(n(', '( n(').replace('))', ') )')
    #Cleanup the == condition
    mod_cond_str = mod_cond_str.replace(' = ', '=').replace(' =', '=').replace('= ', '=')
    T = []
    O = []
    for tok in mod_cond_str.split():
        if tok in ['(', '&', '|']:
            # Add to operator stack
            O.append(tok)
        elif tok == ')':
            prev_op_pop = ""
            o_pop = O.pop()
            while o_pop <> '(':
                if prev_op_pop <> o_pop:
                    t1 = T.pop()
                    t2 = T.pop()
                    T.append( [ o_pop, '(' , t1 , t2 ])
                else:
                    t1 = T.pop()
                    t2 = T.pop()
                    t1.append(t2)
                    T.append(t1)
                prev_op_pop = o_pop
                o_pop = O.pop()
            T[-1].append(')')
        else:
            T.append(tok)
    prev_op_pop = ""
    while(len(O) >0 ):
        o_pop = O.pop()
        if prev_op_pop <> o_pop:
            t1 = T.pop()
            t2 = T.pop()
            T.append( [ o_pop, '(' , t1 , t2 ])
        else:
            t1 = T.pop()
            t2 = T.pop()
            t1.append(t2)
            T.append(t1)
        prev_op_pop = o_pop
    if len(mod_cond_str.split()) > 1:
        try:
            T[-1].append(')')
        except AttributeError:
            print str(T)
    expr = list(flatten(T))
#    print "Received : " + condition + "\t\t\t\t\tPrefix : " + ' '.join(expr)
    return expr

def convertPrefixToDotEdge(jobname, expr, boxnodes, boxedges):
    global nodeIter
    orboxflag = 0
    opStack = []
    tokStack = []
#    dotEdge = []
    for tok in expr:
        if tok == '|':
            orboxflag = 1
            opStack.append(tok)
            continue
        elif tok == '(':
            tokStack.append(tok)
            continue
        elif tok == '&':
            opStack.append(tok)
        elif tok == ')':
            o = opStack.pop()
            t = tokStack.pop()
            try:
                while t <> '(':
                    if o == '&' and orboxflag == 1:
                        #boxedges.append(t + ' -> ANDBOX' + nodeIter)
                        boxedges.append({   "FROM": t.split("(",1)[1].split(")",1)[0],
                                            "TO": "ANDBOX" + str(nodeIter),
                                            "TYPE": t.split("(",1)[0],
                                            "RETURN":t.split("=",1)[1] if len(t.split("=",1)) == 2 else ""
                                            })
                    elif o == '&' and orboxflag == 0:
                        #boxedges.append(t + ' -> ' + jobname)
                        boxedges.append({   "FROM": t.split("(",1)[1].split(")",1)[0],
                                            "TO" : jobname,
                                            "TYPE":t.split("(",1)[0],
                                            "RETURN":t.split("=",1)[1] if len(t.split("=",1)) == 2 else ""
                                            })
                    elif o == '|':
                        #boxedges.append(t + ' -> ORBOX' + nodeIter)
                        boxedges.append({   "FROM": t.split("(",1)[1].split(")",1)[0],
                                            "TO" : "ORBOX" + str(nodeIter),
                                            "TYPE":t.split("(",1)[0],
                                            "RETURN":t.split("=",1)[1] if len(t.split("=",1)) == 2 else ""
                                            })
                    t = tokStack.pop()
            except IndexError:
                print t
            if o == '&' and orboxflag == 1:
                tokStack.append('s(ANDBOX' + str(nodeIter) + ')')
                boxnodes.append({   "NODE" : 'ANDBOX' + str(nodeIter),
                                    "COMMAND": "AND",
                                    "TYPE":"LOGICAL"
                                    })
                nodeIter = nodeIter + 1
            elif o == '|':
                tokStack.append('s(ORBOX' + str(nodeIter) + ')')
                boxnodes.append({   "NODE" : 'ORBOX' + str(nodeIter),
                                    "COMMAND": "OR",
                                    "TYPE" : "LOGICAL"
                                    })
                orboxflag = 0
                nodeIter = nodeIter + 1
        else:
            tokStack.append(tok)
    while len(tokStack) <> 0:
        #dotEdge.append(tokStack.pop() + ' -> ' + jobname)
        t = tokStack.pop()
        boxedges.append({   "FROM": t.split("(",1)[1].split(")",1)[0],
                            "TO": jobname,
                            "TYPE": t.split("(",1)[0],
                            "RETURN":t.split("=",1)[1] if len(t.split("=",1)) == 2 else ""
                            })
    #print "dotEdge generated as : " + str(dotEdge)



def processComplexConditions(jobname, condition, boxnodes, boxedges):
    prefixExprCond = buildPrefixExpression(condition)
    convertPrefixToDotEdge(jobname, prefixExprCond, boxnodes, boxedges)



def paintDependency(deptype):
    if deptype == 's':
        return "color=green"
    if deptype == 'n':
        return "color=black, style=dotted"
    if deptype == 'f':
        return "color=red"
    if deptype == 'e':
        return 'color=red, style=dotted'
    return ""

    
# Open log file
#verboseFile = open('agrajag.' + tstamp + '.log', 'w')
# Open Filewatcher Detail file
#fileWatcherFile = open('FileWatcherList.' + tstamp + '.log', 'w')


# Zero out data structures and counts
jobCount = 0
#dl = [] # List of all jobs. Each job is represented by a dictionary.
tempDict = {}
#boxdl = {}


# Start reading from JIL File

# Final Data Structure format
# boxdl = {
#    "Box1" : [ {    "JOB"       : "Job1",
#                    "BOX_NAME"  : "Box1",
#                    "COMMAND"   : "$BATCH_SCRIPT/job1.ksh",
#                    ...
#                    },
#               ...
#               ]
#    ...
# }

boxdl = {}
for line in args.JILFile:
    toks = line.split(':', 1)
    if len(toks) == 2:
        key = toks[0].strip()
        value = toks[1].strip()
        if key == 'insert_job':
            # Check if this is the first job in the list.
            # If it is, then initialize tempDict and start.
            # Else, close out the previous tempDict, append it to dl, and then reinitialize from the beginning.
            if jobCount <> 0:
                if 'BOX_NAME' in tempDict.keys():
                    if (tempDict["BOX_NAME"].strip() not in boxdl.keys()) and (tempDict["BOX_NAME"].split(".", 1)[1] == "b"):
                        boxdl[tempDict["BOX_NAME"].strip()] = []
                    elif (tempDict["BOX_NAME"].strip() in boxdl.keys()) and (tempDict["BOX_NAME"].split(".", 1)[1] == "b"):
                        boxdl[tempDict["BOX_NAME"].strip()].append(tempDict)
#                dl.append(tempDict)
            jobCount = jobCount + 1
            tempDict = {}
            tempDict["JOB"] = value.split(' ',1)[0].strip()
            tempDict["JOBTYPE"] = value.split(':')[-1].strip()
        if key in [ "box_name", "command", "machine", "owner", "condition", "description", "max_run_alarm", "date_conditions", "watch_file"]:
            tempDict[key.upper()] = value.strip()
# When the JIL is complete, append the last build tempDict dictionary.
#dl.append(tempDict)
#if 'BOX_NAME' in tempDict.keys():
#    if (tempDict["BOX_NAME"].strip() not in boxdl.keys()) and (tempDict["BOX_NAME"].split(".", 1)[1] == "b"):
#        boxdl[tempDict["BOX_NAME"].strip()] = []
##        boxdl[tempDict["BOX_NAME"].strip()].append(tempDict)
#    elif (tempDict["BOX_NAME"].strip() in boxdl.keys()) and (tempDict["BOX_NAME"].split(".", 1)[1] == "b"):
#        boxdl[tempDict["BOX_NAME"].strip()].append(tempDict)

print "Number of Jobs processed : " + str(jobCount)


# Build a list of nodes and edges per box.
nodes = {} # This is a dictionary. With the key = BoxName and value = List of dicts corresponding to boxnodes below.
edges = {} # This is a dictionary. With the key = BoxName and value = List of dicts corresponding to boxedges below.

for box in boxdl.keys():
    boxnodes = [] # This is a list of dicts. The keys of the dict are "JOB", "COMMAND", "TYPE"
    boxedges = [] # This is a list of dicts. The keys of the dict are "FROM", "TO", "TYPE", "RETURN"
    tempNode = {}
    tempEdge = {}
    for job in boxdl[box]:
        tempNode = {}
        tempNode["NODE"] = job["JOB"]
        if job["JOB"][-2:] == ".f":
            if "WATCH_FILE" in job.keys():
                tempNode["TYPE"] = "f"
                tempNode["COMMAND"] = job["WATCH_FILE"]
        else:
            if "COMMAND" in job.keys():
                tempNode["TYPE"] = "s"
                tempNode["COMMAND"] = job["COMMAND"]
            else:
                tempNode["TYPE"] = "u"
                tempNode["COMMAND"] = ""
        boxnodes.append(tempNode)
        if "CONDITION" in job.keys() and len(job["CONDITION"].strip()) > 0 :
            processComplexConditions(job["JOB"], job["CONDITION"], boxnodes, boxedges)
    nodes[box] = boxnodes
    edges[box] = boxedges

print str(nodes)
print str(edges)

# Build dotfile
for box in boxdl.keys():
    df = open(box + ".dot", "w")
    df.write("digraph {\n")
    cluster_number = 0
    df.write("\tsubgraph cluster_" + str(cluster_number) + " {\n")
    df.write('\t\tsize="3,2"; ratio = fill;\n')
    df.write('\t\tstyle=filled;')
    df.write('\t\tcolor=lightgrey;')
    df.write('\t\tfontname="helvetica-bold";')
    df.write('\t\tlabel = "' + box + '"\n')
    df.write("\t\tnode [style=filled, color=white, fontname=helvetica];\n")
    for node in nodes[box]:
            drawparams = ""
            drawshape = "shape=record"
            nodeweight = 'weight=1'
            if node["TYPE"] == 'f':
                drawparams = "color=lightblue" + ","
            elif node["TYPE"] == 'u':
                drawparams = "color=red" + ","
            if node["COMMAND"] in ["AND", "OR"]:
                drawshape = "shape=diamond"
                drawparams = "color=crimson"
                df.write('\t\t\t"' + node["NODE"] + '" [' + drawshape + ', ' + drawparams + ', label="' + node["COMMAND"] +  '"]\n')
            else:
                df.write('\t\t\t"' + node["NODE"] + '" [' + drawshape + ', ' + drawparams + ' label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD><B>' + node["NODE"] + '</B></TD></TR><TR><TD><FONT COLOR="grey15">' + node["COMMAND"].split('/')[-1] + '</FONT></TD></TR></TABLE>>]\n')
    for edge in edges[box]:
        # If edge type is n, then flip the from and to.
        if edge["TYPE"] == "n":
            #nodeweight = 'weight=0.5'
            df.write('\t\t\t"' + edge["TO"] + '" -> "' + edge["FROM"] + '" [' + paintDependency(edge["TYPE"]) + ',' + nodeweight + ']\n')
        else:
            #if edge["TYPE"] == "f":
                #nodeweight = 'weight=0.5'
            #if edge["FROM"][0:3] == 'AND' or edge["FROM"][0:1] == 'OR':
                #nodeweight = 'weight=2'
            df.write('\t\t\t"' + edge["FROM"] + '" -> "' + edge["TO"] + '" [' + paintDependency(edge["TYPE"]) + ',' + nodeweight + ']\n')
    df.write("\t}\n")
    cluster_number = cluster_number + 1
    df.write("}")
    df.close()
    check_call(['dot','-Tjpg',box + '.dot','-o',box + '.jpg'])