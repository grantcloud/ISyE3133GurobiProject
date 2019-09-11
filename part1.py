#Part1CodeFinal

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
    #dictionary where key is arc i --> j and value is capacity of that arc

    m = Model("Deep Space 9")
    m.setParam('OutputFlag', True)


    #Creating all of the decisions variables:
    #1: Creating arc flow decisions variables
    x = m.addVars(decArcs, name = 'energyFlow')

    #2: Creating node energy usage decisions variables:
    y = m.addVars(nodes, name = 'energyUsage')

    #Objective
    objectiveJs = []
    for arc in arcs:
        if arc[0] == '1':
            objectiveJs.append(arc[1]) #adds all j's from node '1' --> j to a list
    m.setObjective(quicksum(x['1',j] for j in objectiveJs), GRB.MAXIMIZE)

    #Constraints:
    #made the assumption that the generator always supplies node 1 to demand, doesn't count towards flow
    m.addConstr(y['1'] == int(demands['1']), name='generator supply')

    #sum of flow on an arc from i --> j + j --> i <= capacity of that arc
    for arc in arcs:
        m.addConstr(x[arc[0],arc[1]] + x[arc[1],arc[0]] <= int(capacities[(arc[0],arc[1])]), name='capacity')

    #nonnegativity constraint:
    #arc flow in any direction is nonnegative
    for arc in decArcs:
        m.addConstr(x[arc[0],arc[1]] >= 0, name='nonnegativity')
    #node energy usage is nonnegative
    for node in nodes:
        m.addConstr(y[node] >= 0, name='nonnegativity')

    #energy used at a node is <= energy demanded at a node:
    for node in nodes:
        m.addConstr(y[node] <= int(demands[node]), name='demands')

    #flow constraints:
    #1: total energy used == energy output by generator plus energy used at the generator node:
    m.addConstr(y['1'] + quicksum(x['1',j] for j in objectiveJs) == quicksum(y[node] for node in nodes))
    #2: flow in = flow out + energy used at all nodes
    for node in nodes:
        nodeArcList = [arc[1] for arc in decArcs if node == arc[0]]
        if node != '1':
            m.addConstr(y[node] + quicksum(x[node,nout] for nout in nodeArcList) == quicksum(x[nin, node] for nin in nodeArcList))

    m.optimize()

    status_code = {1:'LOADED',2:'OPTIMAL',3:'INFEASIBLE',4:'INF_OR_UNBD',5:'UNBOUNDED'}
    status = m.status
    print('The optimization status is {}'.format(status_code[status]))
    if status == 2:
        print('Optimal solution:')
        for v in m.getVars():
            print('%s = %g' % (v.varName, v.x))

    #total flow used
    return sum([var.x for var in m.getVars() if var.varName[0:7] == 'energyU'])
print('Max Flow is:' + str(maxFlow()))
