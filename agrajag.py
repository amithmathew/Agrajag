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

import datetime
import argparse
import re
from subprocess import check_call

# Script Version
VERSION = '0.1'

# Generate datetime
tstamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# Command-line argument parsing
parser = argparse.ArgumentParser(description='Agrajag - Autosys JIL to Graph Translator.', version=VERSION)
parser.add_argument(	'JILFile', 
						metavar='in-file', 
						type=argparse.FileType('rt'),
						help='The JIL .txt file'
				)
args = parser.parse_args()

def processConditions(cond_string):
    cond = ""
    if len(cond_string.strip()) <> 0:
        cond_list = []
        mod_cond_str = cond_string.replace(' and ', '&').replace(' or ', '|')
        conds = re.split('[&]', mod_cond_str)
        for cond in conds:
            cond_dict = {}
            cond_dict["type"] = cond.strip().split('(',1)[0]
            #print cond.strip().split('(', 1)[1].split(')',1)[0]
            cond_dict["dependency"] = cond.strip().split('(', 1)[1].split(')',1)[0]
            cond_list.append(cond_dict)
        return cond_list
    else:
        return ""


def paintDependency(deptype):
    if deptype == 's':
        return "color=green"
    if deptype == 'n':
        return "color=black, style=dotted"
    if deptype == 'f':
        return "color=red"
    return ""

    
# Open log file
verboseFile = open('agrajag.' + tstamp + '.log', 'w')
# Open Filewatcher Detail file
fileWatcherFile = open('FileWatcherList.' + tstamp + '.log', 'w')


# Zero out data structures and counts
jobCount = 0
dl = []
tempDict = {}

# Start reading from JIL File
for line in args.JILFile:
    toks = line.split(':', 1)
    if len(toks) == 2:
        key = toks[0].strip()
        value = toks[1].strip()
        if key in [ "box_name", "command", "machine", "owner", "condition", "description", "max_run_alarm", "date_conditions", "watch_file"]:
            if key == 'condition':
                tempDict[key.upper()] = processConditions(value.strip())
            else:
                tempDict[key.upper()] = value.strip()
        if key == 'insert_job':
            if jobCount <> 0:
                dl.append(tempDict)
            jobCount = jobCount + 1
            tempDict = {}
            tempDict["JOB"] = value.split(' ',1)[0].strip()
            tempDict["JOBTYPE"] = value.split(':')[-1].strip()
dl.append(tempDict)
print "Number of Jobs processed : " + str(jobCount)

boxdl = {}
for job in dl:
    if 'BOX_NAME' in job.keys():
        if (job["BOX_NAME"].strip() not in boxdl.keys()) and (job["BOX_NAME"].split(".",1)[1] == "b"):
            boxdl[job["BOX_NAME"].strip()] = []
            boxdl[job["BOX_NAME"].strip()].append(job)
        elif (job["BOX_NAME"].strip() in boxdl.keys()) and (job["BOX_NAME"].split(".",1)[1] == "b"):
            boxdl[job["BOX_NAME"].strip()].append(job)
            
# Build Subgraphs
cluster_number = 0
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
    for job in boxdl[box]:
        if job["JOB"][-2:] == ".f":
            # Make a list of all filewatcher jobs
            fileWatcherFile.write(job["BOX_NAME"] + " : " + job["JOB"] + " : " + job["WATCH_FILE"] + "\n")
            df.write('\t\t\t"' + job["JOB"] + '" [shape=box, color=lightblue]\n')
        else:
            #df.write('\t\t\t"' + job["JOB"] + '" [shape=record, label="{' + job["JOB"] + ' | ' + job["COMMAND"].split('/')[-1] + '}"]\n')
            df.write('\t\t\t"' + job["JOB"] + '" [shape=record, label=<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4"><TR><TD><B>' + job["JOB"] + '</B></TD></TR><TR><TD><FONT COLOR="grey15">' + job["COMMAND"].split('/')[-1] + '</FONT></TD></TR></TABLE>>]\n')
        if "COMMAND" in job.keys():
            verboseFile.write(job["JOB"] + " : " + job["COMMAND"] + "\n")
        #df.write('\t\t\t"' + job["JOB"] + '" [shape=box]\n')
        if "CONDITION" in job.keys():
            for cond in job["CONDITION"]:
#                    if cond["type"] == 's':
                 if cond["type"] == 'n':
                    df.write('\t\t\t"' + job["JOB"] + '" -> "' + cond["dependency"] + '" [' + paintDependency(cond["type"]) + ']\n')
                 else:
                    df.write('\t\t\t"' + cond["dependency"] + '" -> "' + job["JOB"] + '" [' + paintDependency(cond["type"]) + ']\n')
    df.write("\t}\n")
    cluster_number = cluster_number + 1
    df.write("}")
    df.close()
    check_call(['dot','-Tjpg',box + '.dot','-o',box + '.jpg'])
fileWatcherFile.close()
verboseFile.close()