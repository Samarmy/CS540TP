import numpy as np
import sys
import pandas as pd
import copy
from operator import attrgetter
import random
import time
#my libraries
from blocks_world import Block,Node
from helpers import *
from random import shuffle


def heuristic_coordinates(blockList,goalBlockList,grabbed,grabbedBlock, goalProperties,wildcards,actions,action_blocks):
    blockList.sort(key=lambda x: x.Id)
    goalBlockList.sort(key=lambda x: x.Id)

    diff=0

    #logic for distance 
    for block,goal in zip(blockList, goalBlockList):
        if(goal.coords==()):
            for g in goalBlockList:
                if(g.coords==()):
                        continue
                if(compareCoords(block.coords,g.coords)):

                   if(int(g.coords[2])>0):
                      diff+=3
                   else:
                      diff+=1                  
            continue
        else:
            if(not compareCoords(block.coords,goal.coords)):
                #print(block.Id)
                moves=max((int(abs(int(block.coords[0])-int(goal.coords[0])))),(int(abs(int(block.coords[1])-int(goal.coords[1])))),(int(abs(int(block.coords[2])-int(goal.coords[2])))))
                diff+=moves
                if(int(block.coords[2])!=int(goal.coords[2])  ):
                    if(grabbedBlock!=block.Id):
                                diff+=2
                    else:
                                diff+=1

                slides=[k for k in actions if 'slide' in k]
                blockSlides=[k for k in slides if block.Id in k]
                #print(blockSlides)
                if(blockSlides==[] and int(block.coords[2])==int(goal.coords[2])==0):
                    #print('adsf')
                    if(grabbedBlock!=block.Id):
                                diff+=2
                    else:
                                diff+=1




                
            #print(wildcards)
            #sys.exit()
            if(int(goal.coords[2])>0):
                    foundUnder2=False
                    foundUnder1=False
                    if(int(goal.coords[2])>1):
                        gt1=True
                    else:
                        gt1=False
                    for b in blockList:
                        if(b.Id==block.Id):
                            continue
                        if(int(goal.coords[0])==int(b.coords[0]) and int(goal.coords[1])==int(b.coords[1]) and int(goal.coords[2])-1==int(b.coords[2])):
                            foundUnder1=True
                            #if(grabbedBlock==b.Id):
                                #diff+=1
                        if(gt1):
                            
                            if(int(goal.coords[0])==int(b.coords[0]) and int(goal.coords[1])==int(b.coords[1]) and int(goal.coords[2])-2==int(b.coords[2])):
                                foundUnder2=True
                                #if(grabbedBlock==b.Id):
                                    #diff+=1                            
                        if(int(block.coords[0])==int(b.coords[0]) and int(block.coords[1])==int(b.coords[1]) and int(block.coords[2])<int(b.coords[2])):
                            diff+=3
                    if(not foundUnder1):
                        diff+=3
                    if(not foundUnder2 and gt1):
                        diff+=3
                        
                    if(grabbedBlock==block.Id and not foundUnder1):
                        release=[k for k in actions if 'release' in validActions(Node(blockList,None, grabbed, grabbedBlock),action_blocks)]
                            
                        if(release==[]):
                            diff+=2

    return diff

def heuristic_relationships(blockList,goalBlockList,grabbed,grabbedBlock, goalProperties,wildcards,actions,action_blocks):
    diff=0
    lock=2
    shuffle(goalProperties)
    orig=wildcards
    counts=[s for s in goalProperties if 'on-top-of' in s]
    if(len(counts)>3):
        onTopHeuristic=onTopHeuristic_many
    else:
        onTopHeuristic=onTopHeuristic_original
    for goal in goalProperties:
            g= goal.split()
            if(g[2]=='location' and "wildcard" in g[1]):
                #print(wildcards[g[1]])
                x1=wildcardLocationHeuristic(blockList,wildcards[g[1]] if g[1] in wildcards else None,(g[3],g[4],g[5]))
                if(x1==0):
                    lock=1
                    filledWildcard=next((x for x in blockList if (int(x.coords[0]),int(x.coords[1]),int(x.coords[2])) == (int(g[3]),int(g[4]),int(g[5]))), None)
                    if(filledWildcard!=None):
                        wildcards[g[1]]=[]
                        wildcards[g[1]].append(filledWildcard.Id)
                diff+=x1

            if(g[3]=='side-by-side'):
                x2=sideBySideHeuristic(blockList,wildcards,g[1],g[2])

                diff+=x2
            if(g[3]=='on-top-of'):
                x3,wildcards=onTopHeuristic(blockList,wildcards,g[1],g[2], grabbedBlock,lock,goalProperties,actions)
                diff+=x3

    return diff


def aStarSearch(blockList,goalBlockList, goalProperties,wildcards,action_blocks,heuristic, compare,relationship_actions=False):
    toExplore=[]
    finished=[]

    node=Node(blockList,None)

    goalNode=Node(goalBlockList,None)
    node.action=''
    node.g=0
    node.h=heuristic(node.blockList,goalNode.blockList, False, None, goalProperties,wildcards,[],action_blocks)
    node.f=node.h+node.g
    
    toExplore.append(node)
    while len(toExplore)>0:
        #currentNode = min(toExplore, key=attrgetter('f')) #of all the nodes we need to explore, pick the one with the lowest f value
        m=min(node.h for node in toExplore)
        idx=[i for i, x in enumerate(toExplore) if x.h==m]
        currentNode =toExplore[random.choice(idx)]

        if(relationship_actions):
            if(random.randint(1,100*len(blockList))==2):
                return None,None
        else:

            #Restarts are going to be dependent on the length of the blockList.  If its a larger block list, we want to search longer before restarting. 
            if(random.randint(1,25*len(blockList))==2):
                return None,None

            
        toExplore.remove(currentNode)
        finished.append(currentNode)


        if(compare(currentNode,goalNode,goalProperties,wildcards)):
            commandList = []
            current=currentNode
            while current is not None:
                commandList.append(current.action)
                current = current.parent

            return commandList[::-1],currentNode.blockList # Return reversed path

        #start exploring children of current node
        children=[]


        actions=validActions(currentNode,action_blocks,relationship_actions)

        for action in actions:
            childBlockList,grabbed,grabbedBlock=takeAction(currentNode,action)

            childNode=Node(childBlockList,currentNode,grabbed,grabbedBlock)
            childNode.action=action
            children.append(childNode)
        
        for child in children:
            addToExplore=True

            child.g=currentNode.g+1
            child.h=heuristic(child.blockList,goalNode.blockList, child.grabbed, child.grabbedBlock, goalProperties,wildcards,actions,action_blocks)
            child.f=child.h+child.g

            if(addToExplore):
                toExplore.append(child)




if __name__ == '__main__':

    try:
        start=sys.argv[1]
        goal=sys.argv[2]
    except IndexError:
            start='tests/start.txt'
            goal='tests/goal.txt'

    startState=readFile(start)
    goalState=readFile(goal)
    
    startBlockList=initialize(startState)

    goalBlockList=copy.deepcopy(startBlockList)
    startBlockList=fillInBlockProperties(startState, startBlockList)

    goalBlockList,goalProperties=fillInBlockProperties_Goal(goalState, goalBlockList)
    wildcards=defineWildcards(startBlockList, goalProperties)



    startBlockList.sort(key=lambda x: x.Id)
    goalBlockList.sort(key=lambda x: x.Id)
    print("Start State:")
    printBlockList(startBlockList)
    print("Goal State:")
    printBlockList(goalBlockList)
    print("\nGoal relationships:")

    for i in goalProperties:
        print(i)


    count=0
    for g in goalBlockList:
        if(g.coords!=()):
            count+=1

    minCommandLength=1000
    #print("\nSearching...\n")
    for x in range(10):
        print('Search #'+str(x+1))
        commands=None
        if(count>7):
            action_blocks=get_actions_blocks2(startBlockList, goalBlockList, goalProperties,wildcards)
        else:
            action_blocks=get_actions_blocks(startBlockList, goalBlockList, goalProperties,wildcards)

    
        while(commands==None):
            wildcards=defineWildcards(startBlockList, goalProperties)
            commands,endBlockList=aStarSearch(startBlockList,goalBlockList, goalProperties,wildcards,action_blocks,heuristic_coordinates, compare_coordinates)
        commands=commands[1:]

        #print(compare_coordinates(Node(endBlockList, None), Node(goalBlockList, None),goalProperties,wildcards))
        #printBlockList(endBlockList)
        #sys.exit()

        print("Coordinate search complete. ")
        action_blocks=get_actions_blocks(startBlockList, goalBlockList, goalProperties,wildcards,relationship_actions=True)
        relationship_commands=None
        while(relationship_commands==None):
            wildcards=defineWildcards(startBlockList, goalProperties)
            relationship_commands,endBlockList2=aStarSearch(endBlockList,goalBlockList, goalProperties,wildcards,action_blocks,heuristic_relationships, compare_relationships,relationship_actions=True)
            if(relationship_commands==None):
                print("Restarting...")
        commands.extend(relationship_commands[1:])
        
        if(len(commands)<minCommandLength):
            minCommandLength=len(commands)
            bestCommandList=commands
            print("END STATE:")
            printBlockList(endBlockList2)
            print(bestCommandList)
            print("LENGTH: "+str(len(bestCommandList)))
            print()

        #sys.exit()


print("BEST:")
printBlockList(endBlockList2)
print(bestCommandList)
print("LENGTH: "+str(len(bestCommandList)))






