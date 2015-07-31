import pprint

def procCondition(condition):
    mod_cond_str = condition.replace(' and ', '&').replace(' or ', '|')
    mod_cond_str = mod_cond_str.replace('(s(', '( s(').replace('(f(', '( f(').replace('(n(', '( n(').replace('))', ') )')
    # Shunting Yard Algorithm - http://stackoverflow.com/a/47717
    T = []
    O = []
    final_edges = []
    for tok in mod_cond_str.split():
        if tok in ['(', ')', '&', '|']:
            # Add to operator stack
            if O[-1] == tok:
                O.append(tok)
            if tok == '|':
                t1 = T.pop()
                o1 = O.pop()
                while len(O) > 0 or o1 <> '(':
                    final_edges.append(t1 + '-> ORBOX')
                    t1 = T.pop()
                    o1 = o.pop()
                final_edges.append('ORBOX -> JOB1')
            if tok == ')':
                o1 = o.pop()
                while o1 <> '(':


        else:
            T.append(tok)
    print "Tokens are : " + str(T)
    print "Operators are : " + str(O)


procCondition('(s(A) & s(B)) | s(C)')



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
    T = []
    O = []
    prefixEq = []
    final_edges = []
    i = 0
    for tok in mod_cond_str.split():
#        print "====================================================================="
#        print "Processing " + tok
#        print "====================================================================="
        if tok in ['(', '&', '|']:
            # Add to operator stack
            O.append(tok)
#            print "Pushed Operator onto O stack"
#            print "O Stack : " + str(O)
        elif tok == ')':
#            print "Found parentheses close."
#            print "Starting pop sequence."
            prev_op_pop = ""
            o_pop = O.pop()
#            print "Popped out operator : " + o_pop
            while o_pop <> '(':
#                print "\t\tHave not found Parantheses open yet."
                if prev_op_pop <> o_pop:
#                    print "The current operator : " + o_pop + " does not match the previous operator : " + prev_op_pop
                    t1 = T.pop()
                    t2 = T.pop()
#                    print "Pop out two tokens : " + t1 + " and " + t2
                    T.append( [ o_pop, '(' , t1 , t2 ])
#                    print "Now Stack T is : " + str(T)
                else:
#                    print "The current operator : " + o_pop + " matches the previous operator : " + prev_op_pop
                    t1 = T.pop()
                    t2 = T.pop()
                    t1.append(t2)
#                    print "Add the new token to the existing token list : " + str(t1)
                    T.append(t1)
#                    print "Now Stack T is : " + str(T)
                prev_op_pop = o_pop
                o_pop = O.pop()
#            print "Found closing parantheses. Adding it to the last element in Stack T"
            T[-1].append(')')
#            print "Now Stack T is : " + str(T)
        else:
#            print "Found a token. Adding it to stack T."
            T.append(tok)
#            print "Now Stack T is : " + str(T)

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
        T[-1].append(')')
    OUT = list(flatten(T))
    print "Received : " + condition + "\t\t\t\t\tPrefix : " + ' '.join(OUT)
    return OUT


def convertPrefixToDotEdge(expr):
    orboxflag = 0
    opStack = []
    tokStack = []
    dotEdge = []
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
            while t <> '(':
                if o == '&' and orboxflag == 1:
                    dotEdge.append(t + ' -> ANDBOX')
                elif o == '&' and orboxflag == 0:
                    dotEdge.append(t + ' -> JOB')
                elif o == '|':
                    dotEdge.append(t + ' -> ORBOX')
                t = tokStack.pop()
            if o == '&' and orboxflag == 1:
                tokStack.append('ANDBOX')
            elif o == '|':
                tokStack.append('ORBOX')
                orboxflag = 0
        else:
            tokStack.append(tok)
    while len(tokStack) <> 0:
        dotEdge.append(tokStack.pop() + ' -> JOB')
    print "dotEdge generated as : " + str(dotEdge)

convertPrefixToDotEdge(test('(s(A) & s(B) & s(C)) | s(D)'))
convertPrefixToDotEdge(test('(s(A) | s(B) | s(C)) & s(D) & s(E)'))
convertPrefixToDotEdge(test('s(A) | s(B)'))
convertPrefixToDotEdge(test('s(A)'))
convertPrefixToDotEdge(test('e(A)=45 & s(A)'))





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