#3133 Part 2

import csv
from pprint import pprint
from gurobipy import *


def csvReader(aFile):
    with open(aFile, 'rt') as fin:
        reader = csv.reader(fin)
        header = next(reader)
        return [row for row in reader]

arcList = csvReader('DS9_Network_Arc_Data_B2.csv')
nodeList = csvReader('DS9_Network_Node_Data.csv')
#arcList = csvReader('Test_Network_Arc_Data_B.csv')
#nodeList = csvReader('Test_Network_Node_Data_B.csv')

    #pprint(arcList)
    # arcList Tuple Format = [Node, Node, Line Capacity, maxBolts]
    #pprint(nodeList)
    # nodeList Tuple Format = [Node, Demand, Resident Group Number]


def maxDemand(t):
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
    maxBolts = {(arc[0],arc[1]): arc[3] for arc in arcList}

    m = Model("Deep Space 9")
    m.setParam('OutputFlag', True)


    #Creating all of the decisions variables:
    #1: Creating arc flow decisions variables
    x = m.addVars(decArcs, name = 'energyFlow')
    #2: Creating node energy usage decisions variables:
    y = m.addVars(nodes, name = 'energyUsage')
    #creating all new variables for ILP section
    b = m.addVars(arcs, vtype = GRB.INTEGER, name = 'bolts')
    d = m.addVars(arcs, vtype = GRB.BINARY, name = 'binary')

    #NEW PARAMETERS
    #t = arbitrary number of hours available for the engineering team (unlimited) in cas one
    # k[i,j] == max number of bolts that can be added to arc i,j
    k = maxBolts

    #objective
    objectiveJs = []
    for i,j in arcs:
        if i == '1':
            objectiveJs.append(j) #adds all j's from node '1' --> j to a list
    m.setObjective(quicksum(x['1',j] for j in objectiveJs), GRB.MAXIMIZE)

    #Constraints:
    m.addConstr(y['1'] == int(demands['1']), name='generator supply')

    #total engineering hours used is less than engineering Hours available
    m.addConstr(quicksum(3 * d[i,j] + b[i,j] for i,j in arcs) <= t, "totalEngineeringHours")

    # bolts added is less than or equal to max bolts able to be added
    for i,j in arcs:
        m.addConstr(b[i,j] <= d[i,j] * k[i,j], "maxBolts")

    #sum of flow on an arc from i --> j + j --> i <= capacity of that arc
    for i,j in arcs:
        m.addConstr(x[i,j] + x[j,i] <= int(capacities[(i,j)]) + b[i,j], name='capacity')

    #nonnegativity constraint:
    #arc flow in any direction is nonnegative
    for i,j in arcs:
        m.addConstr(x[i,j] >= 0, name='nonnegativity')
    #node energy usage is nonnegative
    for j in nodes:
        m.addConstr(y[j] >= 0, name='nonnegativity')
    #bolts added cant be negative
    for i,j in arcs:
        m.addConstr(b[i,j] >= 0, "nonnegativity")

    #energy used at a node is <= energy demanded at a node:
    for j in nodes:
        m.addConstr(y[j] <= int(demands[j]), name='demands')

    #flow constraints:
    #1: total energy used == energy output by generator plus energy used at the generator node:
    m.addConstr(y['1'] + quicksum(x['1',j] for j in objectiveJs) == quicksum(y[node] for node in nodes))
    #2: flow in = flow out + energy used at all nodes
    for j in nodes:
        nodeArcList = [arc[1] for arc in decArcs if j == arc[0]]
        if j != '1':
            m.addConstr(y[j] + quicksum(x[j,i] for i in nodeArcList) == quicksum(x[i, j] for i in nodeArcList))

    m.optimize()

    status_code = {1:'LOADED',2:'OPTIMAL',3:'INFEASIBLE',4:'INF_OR_UNBD',5:'UNBOUNDED'}
    status = m.status
    print('The optimization status is {}'.format(status_code[status]))
    if status == 2:
        print('Optimal solution:')
        for v in m.getVars():
            #continue
            print('%s = %g' % (v.varName, v.x))
    for i in range(5):
        print('     - -     ')
    print("Max engineering hours possible: {}".format((3 * len(arcs) + sum(int(k[i,j]) for i,j in k))))
    return sum([var.x for var in m.getVars() if var.varName[0:7] == 'energyU'])

print("Max possible demand satisfied: " + str(maxDemand(387)))

valueList = []
for num in range(40,81):
    valueList.append((num, maxDemand(num)))

'''
print('Theoretical max demand met is: ' + str(a))
with open('part2csv.csv','wt') as fout:
    writer = csv.writer(fout, delimiter =',')
    for value in valueList:
        print('Engineering hours = {}   ::   Demand met = {}'.format(value[0],value[1]))
        #writer.writerow(value)
    print('csv written')
'''
