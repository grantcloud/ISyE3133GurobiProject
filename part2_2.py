#3133 Part 1

import csv
from pprint import pprint
from gurobipy import *


def csvReader(aFile):
    with open(aFile, 'rt') as fin:
        reader = csv.reader(fin)
        header = next(reader)
        return [row for row in reader]

arcList = csvReader('DS9_Network_Arc_Data.csv')
nodeList = csvReader('DS9_Network_Node_Data.csv')

    #pprint(arcList)
    # arcList Tuple Format = [Node, Node, Line Capacity]
    #pprint(nodeList)
    # nodeList Tuple Format = [Node, Demand, Resident Group Number]

def maxFlow():
    #Cleaning up the data:
    nodes = [node[0] for node in nodeList]
    #list of nodes
    demands = {node[0]: node[1] for node in nodeList}
    #dictionary where key is node num and value is demand at that node
    nodeGroups = {node[0]: node[2] for node in nodeList}
    #dictionary where key is node num and value is group id
    arcs = [(arc[0], arc[1]) for arc in arcList]
    #list of every arc i --> j
    decArcs = arcs + [(arc[1],arc[0]) for arc in arcList]
    #list every arc i --> j and same arcs j --> i
    capacities = {(arc[0],arc[1]): arc[2] for arc in arcList}
    #dictionary where key is arc i --> j and value is capacity of that arc both Directions

    m = Model("Deep Space 9")
    m.setParam('OutputFlag', True)


    #Creating all of the decisions variables:
    #1: Creating arc flow decisions variables
    x = m.addVars(decArcs, name = 'energyFlow')

    #2: Creating node energy usage decisions variables:
    y = m.addVars(nodes, name = 'energyUsage')

    #Objective
    objectiveJs = []
    for i,j in arcs:
        if i == '1':
            objectiveJs.append(j) #adds all j's from node '1' --> j to a list
    m.setObjective(quicksum(x['1',j] for j in objectiveJs), GRB.MAXIMIZE)

    #Constraints:
    m.addConstr(y['1'] == int(demands['1']), name='generator supply')

    #sum of flow on an arc from i --> j + j --> i <= capacity of that arc
    for i,j in arcs:
        m.addConstr(x[i,j] + x[j,i] <= int(capacities[(i,j)]), name='capacity')

    #nonnegativity constraint:
    #arc flow in any direction is nonnegative
    for i,j in arcs:
        m.addConstr(x[i,j] >= 0, name='nonnegativity')
    #node energy usage is nonnegative
    for j in nodes:
        m.addConstr(y[j] >= 0, name='nonnegativity')

    #energy used at a node is <= energy demanded at a node:
    for j in nodes:
        m.addConstr(y[j] <= int(demands[j]), name='demands')

    #flow constraints:
    #1: total energy used == energy output by generator plus energy used at the generator node:
    m.addConstr(y['1'] + quicksum(x['1',j] for j in objectiveJs) == quicksum(y[j] for j in nodes))
    #2: flow in = flow out + energy used at all nodes
    for i in nodes:
        nodeArcList = [arc[1] for arc in decArcs if i == arc[0]]
        if i != '1':
            m.addConstr(y[i] + quicksum(x[i,j] for j in nodeArcList) == quicksum(x[j, i] for j in nodeArcList))

    m.optimize()

    status_code = {1:'LOADED',2:'OPTIMAL',3:'INFEASIBLE',4:'INF_OR_UNBD',5:'UNBOUNDED'}
    status = m.status
    print('The optimization status is {}'.format(status_code[status]))
    if status == 2:
        print('Optimal solution:')
        for v in m.getVars():
            #continue
            print('%s = %g' % (v.varName, v.x))


    #################################
    #################################
    # PART B.1 #2 #

    #building a dictionary where the keys are each groupid and the values are lists of every node in that group
    groupDict = {}
    for value in nodeGroups.values():
        if value not in groupDict.keys():
            groupDict[value] = []
    for node in nodeList:
        groupDict[node[2]].append(node[0])
    groups = groupDict.keys()

    groupMetricList = []
    groupNumMetricList = []
    for group in groupDict:
        groupMetricList.append(sum(y[j].x for j in groupDict[group])/sum([int(demands[j]) for j in groupDict[group]]))
        groupNumMetricList.append(('Group ' + str(group) + ' ratio:',str(sum(y[j].x for j in groupDict[group])/sum([int(demands[j]) for j in groupDict[group]]))))
    z = min(groupMetricList)
    for i in range(3):
        print(' ')
    print("FAIRNESS RATINGS FOR PART B1.1a) MAX FLOW PROBLEM")
    pprint(groupNumMetricList)
    pprint('Fairness Metric: {}'.format(z))

    #total flow used
    return sum([var.x for var in m.getVars() if var.varName[0:7] == 'energyU'])
print('Max Flow is:' + str(maxFlow()))

for i in range(3):
    print(' ')
print('PART B.1 #2')

def fairnessFlow():
    nodes = [node[0] for node in nodeList] #list of nodes
    demands = {node[0]: node[1] for node in nodeList} #dictionary where key is node num and value is demand at that node
    nodeGroups = {node[0]: node[2] for node in nodeList} #dictionary where key is node num and value is group id
    #building a dictionary where the keys are each groupid and the values are lists of every node in that group
    groupDict = {}
    for value in nodeGroups.values():
        if value not in groupDict.keys():
            groupDict[value] = []
    for node in nodeList:
        groupDict[node[2]].append(node[0])
    groups = groupDict.keys()

    arcs = [(arc[0], arc[1]) for arc in arcList] #list of every arc i --> j
    decArcs = arcs + [(arc[1],arc[0]) for arc in arcList] #list every arc i --> j and same arcs j --> i
    capacities = {(arc[0],arc[1]): arc[2] for arc in arcList} #dictionary where key is arc i --> j and value is capacity of that arc

    m = Model("Deep Space 9 pt.2")
    m.setParam('OutputFlag', True)


    #Creating all of the decisions variables:
    #1: Creating arc flow decisions variables
    x = m.addVars(decArcs, name = 'energyFlow')

    #2: Creating node energy usage decisions variables:
    y = m.addVars(nodes, name = 'energyUsage')

    ####NEW FOR PART 2 LINES####
    #3: Creating the z variable described above
    z = m.addVar(name = 'fairnessMetric')

    #Objective
    objectiveJs = []
    for i,j in arcs:
        if i == '1':
            objectiveJs.append(j) #adds all j's from node '1' --> j to a list

    #new objective
    m.setObjective(z, GRB.MAXIMIZE)

    #Constraints:
    #made the assumption that the generator always supplies node 1 to demand, doesn't count towards flow
    m.addConstr(y['1'] == int(demands['1']), name='generator supply')

    #sum of flow on an arc from i --> j <= capacity of that arc
    for i,j in arcs:
        m.addConstr(x[i,j] + x[j,i] <= int(capacities[(i,j)]), name='capacity')


    #nonnegativity constraint:
    #arc flow in any direction is nonnegative
    for i,j in decArcs:
        m.addConstr(x[i,j] >= 0, name='nonnegativity')
    #node energy usage is nonnegative
    for j in nodes:
        m.addConstr(y[j] >= 0, name='nonnegativity')

    #z nonnegativity:
    m.addConstr(z >= 0, name='nonnegativity')

    #energy used at a node is <= energy demanded at a node:
    for j in nodes:
        m.addConstr(y[j] <= int(demands[j]), name='demands')

    #flow constraints:
    #1: total energy used == energy output by generator plus energy used at the generator node:
    m.addConstr(y['1'] + quicksum(x['1',j] for j in objectiveJs) == quicksum(y[node] for node in nodes))
   #2: flow in = flow out + energy used at all nodes
    for i in nodes:
        nodeArcList = [arc[1] for arc in decArcs if i == arc[0]]
        if i != '1':
            m.addConstr(y[i] + quicksum(x[i,j] for j in nodeArcList) == quicksum(x[j, i] for j in nodeArcList))

    #new z constraint:
    for group in groupDict.keys():
        m.addConstr(z <= (quicksum(y[node] for node in groupDict[group])/sum([int(demands[node]) for node in groupDict[group]])), name='zConstraint')

    #THIS IS THE ADDED CONSTRAINT FOR PART B.1 #2 b)
    #demand satisfied >95% of the possible satisfied --> flow out is >= .95(max flow out)
    m.addConstr(quicksum(x['1',j] for j in objectiveJs) + y['1'] >= .95*103, name = '')

    m.optimize()

    status_code = {1:'LOADED',2:'OPTIMAL',3:'INFEASIBLE',4:'INF_OR_UNBD',5:'UNBOUNDED'}
    status = m.status
    print('The optimization status is {}'.format(status_code[status]))
    if status == 2:
        print('Optimal solution:')
        for v in m.getVars():
            #continue
            print('%s = %g' % (v.varName, v.x))

    groupDict = {}
    for value in nodeGroups.values():
        if value not in groupDict.keys():
            groupDict[value] = []
    for node in nodeList:
        groupDict[node[2]].append(node[0])

    #fairness metric
    groupMetricList = []
    groupNumMetricList = []
    for group in groupDict:
        groupMetricList.append(sum(y[node].x for node in groupDict[group])/sum([int(demands[node]) for node in groupDict[group]]))
        groupNumMetricList.append(('Group ' + str(group) + ' ratio:',str(sum(y[node].x for node in groupDict[group])/sum([int(demands[node]) for node in groupDict[group]]))))
    fairnessMetric = min(groupMetricList)
    for i in range(3):
        print(' ')
    print("FAIRNESS RATINGS FOR PART B1.1 c) and B1.2a) MAX FAIRNESS CODE")
    pprint(groupNumMetricList)
    pprint('Fairness Metric: {}'.format(fairnessMetric))

    #total flow used
    return sum([var.x for var in m.getVars() if var.varName[0:7] == 'energyU'])


pprint('Fairness Flow is:' + str(fairnessFlow()))

