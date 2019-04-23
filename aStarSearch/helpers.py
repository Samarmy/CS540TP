import numpy as np
import sys
import pandas as pd
import copy
from operator import attrgetter
from random import shuffle
from blocks_world import Block,Node

#Read input file
def readFile(file):
    with open(file) as f:
        content = f.readlines()

    content = [x.strip() for x in content]
    content = [x.strip('(') for x in content ]
    content = [x.strip(')') for x in content ]

    return content

#This finds all the blocks listed in the startState without repeating and adds to list.
def initialize(state):
    startBlockList=[]
    alreadyAdded=[]
    for i in state:
        j=i.split()
        if(j[0]=='has'):
            if(j[1] not in alreadyAdded):
                startBlockList.append(Block(j[1]))
                alreadyAdded.append(j[1])
            continue
        if(j[1] not in alreadyAdded):
            startBlockList.append(Block(j[1]))
            alreadyAdded.append(j[1])
        if(j[2] not in alreadyAdded):
            startBlockList.append(Block(j[2]))
            alreadyAdded.append(j[2])

    return startBlockList

def printBlockList(blockList):
    df=pd.DataFrame(columns = ['Block','Coordinates', 'Properties'])
    for b in blockList:
        df = df.append({'Block': b.Id,'Coordinates':b.coords,'Properties':b.props}, ignore_index=True)
    df.set_index('Block', inplace=True)
    print(df)


def printNodeInfo(currentNode):
    df=pd.DataFrame(columns = ['Block','Next-to','On-top-of','Level', 'Coordinates', 'Properties'])
    for b in currentNode.blockList:
        df = df.append({'Block': b.Id,'Next-to':b.sides, 'On-top-of':b.onTopOf,'Level':b.height,'Coordinates':b.coords,'Properties':b.props}, ignore_index=True)
    df.set_index('Block', inplace=True)
    print(df)
    print("Grabbed: "+str(currentNode.grabbed))
    print("GrabbedBlock: " +str(currentNode.grabbedBlock))


def fillInBlockProperties_Goal(file, blockList):
    goalRelationships=[]
    for i in file:
        j= i.split()
        
        if(j[0]=='is'):
            goalRelationships.append(i)

        else:
            if(j[3]=='on-top-of'):
                block=next((x for x in blockList if x.Id == j[1]), None)
                
                block.onTopOf=j[2]
            elif(j[3]=='side-by-side'):
                block=next((x for x in blockList if x.Id == j[1]), None)
                block.addSide(j[2])
                block=next((x for x in blockList if x.Id == j[2]), None)
                block.addSide(j[1])

            elif(j[2]=='location' and ('wildcard' not in j[1])):
                block=next((x for x in blockList if x.Id == j[1]), None)
                block.addLocation(j[3],j[4],j[5])
            else:
                goalRelationships.append(i)



    return blockList,goalRelationships




def fillInBlockProperties(file, blockList,goal=False):
    #printBlockList(blockList)
    for i in file:
        j= i.split()
        if(j[2]=='location'):
            block=next((x for x in blockList if x.Id == j[1]), None)
            block.addLocation(j[3],j[4],j[5])
        else:
            block=next((x for x in blockList if x.Id == j[1]), None)
            block.addProp(j[3])

    #blockList=checkIfStackedAndSideBySide(blockList)
    if(goal):
        for i in blockList:
            if(i.sides==[]):
                i.sides='Any'
            if(i.onTopOf==None):
                i.onTopOf='Any'
    #blockList=computeHeight(blockList)
    return blockList




def validSlides_coords(blockList, action_blocks):
    #printBlockList(blockList)
    validBlocks=[]
    for b in blockList:
        if(int(b.coords[2])==0):
            validBlocks.append(b)
    valid=[]
    for i in validBlocks:
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                if(x==0 and y==0):
                    continue


                iNewCoordsX=int(i.coords[0])+int(x)
                iNewCoordsY=int(i.coords[1])+int(y)
                if(iNewCoordsX>9 or iNewCoordsX<0):
                    continue
                if(iNewCoordsY>9 or iNewCoordsY<0):
                    continue

                #check whether another block is occupying spacec
                occupied=False
                for block in blockList:
                    if(int(block.coords[0])==iNewCoordsX and int(block.coords[1])==iNewCoordsY):
                        occupied=True
                if(not occupied):
                    if(i.Id in action_blocks):
                        valid.append('command slide '+str(i.Id)+' '+str(x)+' '+str(y))
    return valid

def validGrabs(blockList, action_blocks):

    validBlocks=[]
    invalid=[]
    valid=[]
    for b in blockList:
        for b2 in blockList:
            if(b.Id==b2.Id):
                continue
            if(int(b.coords[0])==int(b2.coords[0]) and int(b.coords[1])==int(b2.coords[1])):
                if(int(b.coords[2])<int(b2.coords[2])):

                    invalid.append(b.Id)
    for b in blockList:
        if(b.Id not in invalid):
            validBlocks.append(b)
    
    
    for i in validBlocks:
        if(i.Id in action_blocks):
            valid.append('command grab '+str(i.Id))

    return valid



def validCarry(blockList, action_blocks,grabbedBlock):
    grabbed=None
    valid=[]
    #only want to carry to z coordinates where it is possible we can release, limiting z-space
    maxZ=0
    for b in blockList:
        if(int(b.coords[2])>maxZ):
            maxZ=int(b.coords[2])

        
    for i in blockList:
        if(i.Id==grabbedBlock):
            grabbed=i
            break;
    for x in [-1,0,1]:
        for y in [-1,0,1]:
            for z in [-1,0,1]:
                if(x==0 and y==0 and z==0):
                    continue
                iNewCoordsX=int(int(grabbed.coords[0])+int(x))
                iNewCoordsY=int(int(grabbed.coords[1])+int(y))
                iNewCoordsZ=int(int(grabbed.coords[2])+int(z))
                if(iNewCoordsX>9 or iNewCoordsX<0):
                    continue
                if(iNewCoordsY>9 or iNewCoordsY<0):
                    continue
                if(iNewCoordsZ<0):
                    continue
                if(iNewCoordsZ>(maxZ+3)):
                    continue
                #check whether another block is occupying space
                occupied=False
                for block in blockList:
                    if(int(block.coords[0])==iNewCoordsX and int(block.coords[1])==iNewCoordsY and int(block.coords[2])==iNewCoordsZ):
                        occupied=True
                if(not occupied):
                    if(i.Id in action_blocks):
                        valid.append('command carry '+str(i.Id)+' '+str(x)+' '+str(y)+' '+str(z))
    return valid


def validRelease(blockList, action_blocks,grabbedBlock):
    #need to check whether valid release pt.
    g=next((x for x in blockList if x.Id == grabbedBlock), None)
    
    if(int(g.coords[2])==0):
        if(g.Id in action_blocks):
           
            return ['command release '+str(g.Id)]
    else:
        for i in blockList:
            if(int(i.coords[0])==int(g.coords[0]) and int(i.coords[1])==int(g.coords[1]) and int(i.coords[2])==int(g.coords[2])-1):
                if(g.Id in action_blocks):
                    
                    return ['command release '+str(g.Id)]
            
    return []




def get_actions_blocks(startBlockList, goalBlockList, goalProperties,wildcards,relationship_actions=False):
    gl=[]
    
    if(relationship_actions):
        for key, value in wildcards.items():
            for v in value:
                block=next((x for x in goalBlockList if x.Id == v), None)
                if(block.coords==()):
                    gl.append(v)
        for w in goalProperties:
            bs=w.split()
            block=next((x for x in goalBlockList if x.Id == bs[1]), None)
            if(bs[1] not in gl and "wildcard" not in bs[1] and "block" in bs[1] and block.coords==()):
                gl.append(bs[1])
            block=next((x for x in goalBlockList if x.Id == bs[2]), None)
            if(bs[2] not in gl and "wildcard" not in bs[2] and "block" in bs[2] and block.coords==()):
                gl.append(bs[2])
                
        for s in startBlockList:
            for g in gl:
                block=next((x for x in startBlockList if x.Id ==g), None)
                if(int(s.coords[0])==int(block.coords[0]) and int(s.coords[1])==int(block.coords[1]) and block.Id!=s.Id):
                    gl.append(s.Id)
        #print(gl)
        #sys.exit()
        
    else:
        for b in goalBlockList:
            #if(b.coords!=()):
                gl.append(b.Id)
    return gl


def get_actions_blocks2(startBlockList, goalBlockList, goalProperties,wildcards,relationship_actions=False):
    gl=[]
    
    if(relationship_actions):
        for key, value in wildcards.items():
            for v in value:
                block=next((x for x in goalBlockList if x.Id == v), None)
                if(block.coords==()):
                    gl.append(v)
        for w in goalProperties:
            bs=w.split()
            block=next((x for x in goalBlockList if x.Id == bs[1]), None)
            if(bs[1] not in gl and "wildcard" not in bs[1] and "block" in bs[1] and block.coords==()):
                gl.append(bs[1])
            block=next((x for x in goalBlockList if x.Id == bs[2]), None)
            if(bs[2] not in gl and "wildcard" not in bs[2] and "block" in bs[2] and block.coords==()):
                gl.append(bs[2])
                
        for s in startBlockList:
            for g in gl:
                block=next((x for x in startBlockList if x.Id ==g), None)
                if(int(s.coords[0])==int(block.coords[0]) and int(s.coords[1])==int(block.coords[1]) and block.Id!=s.Id):
                    gl.append(s.Id)
        #print(gl)
        #sys.exit()
        
    else:
        for b,a in zip(goalBlockList,startBlockList):
                if(b.coords!=() and not compareCoords(b.coords, a.coords)):
                    gl.append(b.Id)
    return gl
            


def validActions(currentNode, action_blocks,relationship_actions=False):
        import random
        valid=[]
        if(currentNode.grabbed):
            valid.extend(validRelease(currentNode.blockList, action_blocks, currentNode.grabbedBlock))
            
            carry=validCarry(currentNode.blockList, action_blocks,currentNode.grabbedBlock)
            valid.extend(carry)
        else:
            slide=validSlides_coords(currentNode.blockList, action_blocks)

            valid.extend(validGrabs(currentNode.blockList, action_blocks))
            '''if(relationship_actions):
                if(len(slide)>10):
                    slide=[slide[i] for i in random.sample(range(len(slide)), 5)]'''
            valid.extend(slide)
        #print(valid)
        return valid





def takeAction(currentNode,action):
    currentNode=copy.deepcopy(currentNode)
    action=action.split()[1:] 
    if(action[0]=='grab'):
        currentNode.grabbed=True
        currentNode.grabbedBlock=action[1]

    if(action[0]=='release'):
        block=next((x for x in currentNode.blockList if x.Id == action[1]), None)
        currentNode.grabbed=False
        currentNode.grabbedBlock=None

    if(action[0]=='carry'):
        block=next((x for x in currentNode.blockList if x.Id == action[1]), None)
        block.coords=(int(int(block.coords[0])+int(action[2])),int(int(block.coords[1])+int(action[3])),int(int(block.coords[2])+int(action[4])))

    if(action[0]=='slide'):
        slideList=[]
        block=next((x for x in currentNode.blockList if x.Id == action[1]), None)
        for b in currentNode.blockList:
            if(b.Id==action[1]):
                slideList.append(b.Id)
            elif(int(b.coords[0])==int(block.coords[0]) and int(b.coords[1])==int(block.coords[1])):
                slideList.append(b.Id)
        for b in currentNode.blockList:
            if(b.Id in slideList):
                b.coords=(int(int(b.coords[0])+int(action[2])),int(int(b.coords[1])+int(action[3])),b.coords[2])


    return currentNode.blockList, currentNode.grabbed,currentNode.grabbedBlock


def sideBySideCompare(blockList,wildcards,b1,b2):
    valid1=[]
    valid2=[]
    if("wildcard" in b1):
        if(b1 in wildcards.keys()):
            valid1.extend(wildcards[b1])
        else:
            for i in blockList:
                valid1.append(i.Id)
    else:
        valid1.append(b1)

    if("wildcard" in b2):
        if(b2 in wildcards.keys()):
            valid2.extend(wildcards[b2])
        else:
            for i in blockList:
                valid2.append(i.Id)
    else:
        valid2.append(b2)

    
    for a in valid1:
        for b in valid2:
            block1=next((x for x in blockList if x.Id == a), None)
            block2=next((x for x in blockList if x.Id == b), None)
            if(int(block1.coords[2])!=int(block2.coords[2])):
                continue
            else:
                if((abs(int(block1.coords[0])-int(block2.coords[0]) )==1 and  abs(int(block1.coords[1])-int(block2.coords[1]))==0) or (abs(int(block1.coords[0])-int(block2.coords[0]) )==0 and  abs(int(block1.coords[1])-int(block2.coords[1]))==1)):
                   return True
    return False




def sideBySideHeuristic(blockList,wildcards,b1,b2):
    valid1=[]
    valid2=[]
    if("wildcard" in b1):
        if(b1 in wildcards.keys()):
            valid1.extend(wildcards[b1])
        else:
            for i in blockList:
                valid1.append(i.Id)
    else:
        valid1.append(b1)

    if("wildcard" in b2):
        if(b2 in wildcards.keys()):
            valid2.extend(wildcards[b2])
        else:
            for i in blockList:
                valid2.append(i.Id)
    else:
        valid2.append(b2)

    minDist=1000
    for a in valid1:
        for b in valid2:
            block1=next((x for x in blockList if x.Id == a), None)
            block2=next((x for x in blockList if x.Id == b), None)
            if(int(block1.coords[2])==0 and int(block2.coords[2])==0):
                if((int(abs(int(block1.coords[0])-int(block2.coords[0]))))==0 and  (int(abs(int(block1.coords[1])-int(block2.coords[1])))==1) or (int(abs(int(block1.coords[0])-int(block2.coords[0]))))==1 and  (int(abs(int(block1.coords[1])-int(block2.coords[1])))==0)):
                    dist=0
                else:
                    dist=max((int(abs(int(block1.coords[0])-int(block2.coords[0])))),(int(abs(int(block1.coords[1])-int(block2.coords[1])))))
            else:
                dist=max((int(abs(int(block1.coords[0])-int(block2.coords[0])))),(int(abs(int(block1.coords[1])-int(block2.coords[1])))),(int(abs(int(block1.coords[2])-int(block2.coords[1])))))+2
            if(dist<minDist):
                minDist=dist
    return minDist      
    
def onTopHeuristic_many(blockList,wildcards,b1,b2,grabbedBlock,lock,goalProperties,actions):
    blockList=copy.deepcopy(blockList)
    valid1=[]
    valid2=[]
    if("wildcard" in b1):
        if(b1 in wildcards.keys()):
            valid1.extend(wildcards[b1])
        else:
            for i in blockList:
                valid1.append(i.Id)
    else:
        valid1.append(b1)

    if("wildcard" in b2):
        if(b2 in wildcards.keys()):
            valid2.extend(wildcards[b2])
        else:
            for i in blockList:
                valid2.append(i.Id)
    else:
        valid2.append(b2)

    shuffle(valid1)
    shuffle(valid2)

    processed=[]
    minDist=1000
    for a in valid1:
        for b in valid2:
            dist=0
            if(a==b):
                continue
            block1=next((x for x in blockList if x.Id == a), None)
            block2=next((x for x in blockList if x.Id == b), None)

            dist=max(abs(int(block1.coords[0])-int(block2.coords[0])),abs(int(block1.coords[1])-int(block2.coords[1])),abs(int(block1.coords[2])-int(block2.coords[2]))+1)
            if(int(block1.coords[2])==int(block2.coords[2])+1):
                onTop=True
            else:
                onTop=False
                
            if(grabbedBlock!=None):
                if(grabbedBlock==block1.Id):
                        dist+=1
                else:
                        dist+=3
            else:
                    dist+=2
            foundAnother=False
            if(not onTop):

                for i in goalProperties:
                    if(i.split()[3]=='on-top-of'):
                        if(block2.Id==i.split()[1]):
                           aD=next((x for x in blockList if x.Id == i.split()[2]), None)
                           #dist,wildcards=onTopHeuristic(blockList,wildcards,aD,i.split()[2],grabbedBlock,lock,goalProperties,actions)
                           dist=max(abs(int(block2.coords[0])-int(aD.coords[0])),abs(int(block2.coords[1])-int(aD.coords[1])),abs(int(block2.coords[2])-int(aD.coords[2]))+1)
                           for j in goalProperties:
                                    if(j.split()[3]=='on-top-of'):
                                        if(aD.Id==j.split()[1]):
                                           foundAnother=True
                                           aD2=next((x for x in blockList if x.Id == j.split()[2]), None)
                                           #dist,wildcards=onTopHeuristic(blockList,wildcards,aD,i.split()[2],grabbedBlock,lock,goalProperties,actions)
                                           dist=max(abs(int(aD.coords[0])-int(aD2.coords[0])),abs(int(aD.coords[1])-int(aD2.coords[1])),abs(int(aD.coords[2])-int(aD2.coords[2]))+2)
                if(foundAnother):
                        if(grabbedBlock!=None):
                            if(grabbedBlock==block1.Id):
                                    dist+=1
                            else:
                                    dist+=3
                        else:
                                dist+=2

            if(int(block1.coords[0])==int(block2.coords[0]) and int(block1.coords[1])==int(block2.coords[1]) and int(block1.coords[2])-int(block2.coords[2])==1 and not foundAnother):
                return 0, wildcards


                                
                                


            #block1=next((x for x in blockList if x.Id == a), None)
            for bl in blockList:
                if(bl.Id==block1.Id):
                    continue
                if(bl.Id in processed):
                    continue
                if(int(block1.coords[0])==int(bl.coords[0]) and int(block1.coords[1])==int(bl.coords[1]) and int(block1.coords[2])<int(bl.coords[2])):
                    dist+=int(bl.coords[2])+2
                    if(grabbedBlock==bl.Id):
                        dist-=1
            dropDist=10000
            if(grabbedBlock!=None and grabbedBlock!='' and grabbedBlock!=block1.Id and grabbedBlock!=block2.Id):
                release=[s for s in actions if 'release' in s]
                #print("GETS IN HERE")
                gB=next((x for x in blockList if x.Id == grabbedBlock), None)
                if(release==[] and gB.Id!=block1.Id):
                    #print(grabbedBlock)
                    for bl in blockList:
                        #print(gB)
                        if(bl.Id==gB.Id):
                            continue
                        if(int(gB.coords[0])==int(bl.coords[0]) and int(gB.coords[1])==int(bl.coords[1]) and int(gB.coords[2])>int(bl.coords[2])):
                            temp=int(gB.coords[2])-int(bl.coords[2])-1
                            if(temp<dropDist):
                                dropDist=temp
                        '''for i in goalProperties:
                            if(i.split()[3]=='on-top-of'):
                                if(gB.Id==i.split()[1]):
                                    dropDist=5'''
                    if(dropDist==10000):
                        dropDist=int(gB.coords[2])
                        dist+=dropDist


                
            #print(dist)    
            if(dist<minDist):
                minDist=dist
                if("wildcard" in b1):
                    wildcards[b1]=[a]
                    minBlockOntop=a
                if("wildcard" in b2):
                    wildcards[b2]=[b]

    return minDist,wildcards              




def onTopHeuristic_original(blockList,wildcards,b1,b2,grabbedBlock,lock,goalProperties,actions):
    blockList=copy.deepcopy(blockList)
    valid1=[]
    valid2=[]
    if("wildcard" in b1):
        if(b1 in wildcards.keys()):
            valid1.extend(wildcards[b1])
        else:
            for i in blockList:
                valid1.append(i.Id)
    else:
        valid1.append(b1)

    if("wildcard" in b2):
        if(b2 in wildcards.keys()):
            valid2.extend(wildcards[b2])
        else:
            for i in blockList:
                valid2.append(i.Id)
    else:
        valid2.append(b2)

    shuffle(valid1)
    shuffle(valid2)

    processed=[]
    minDist=1000
    for a in valid1:
        for b in valid2:
            dist=0
            if(a==b):
                continue
            block1=next((x for x in blockList if x.Id == a), None)
            block2=next((x for x in blockList if x.Id == b), None)
            if(int(block2.coords[0])==int(block1.coords[0]) and int(block2.coords[1])==int(block1.coords[1]) and int(block2.coords[2])>int(block1.coords[2])):
                dist=max(abs(int(block1.coords[0])-int(block2.coords[0])),abs(int(block1.coords[1])-int(block2.coords[1])),abs(int(block1.coords[2])-int(block2.coords[2])))
                if(dist==1):
                    dist=2
                    if(grabbedBlock!=None):
                        if(grabbedBlock==block2.Id):
                            dist+=3
                        else:
                            dist+=5
                    else:
                        dist+=4
                    
                elif(dist==2):
                    dist=5
                    if(grabbedBlock!=None):
                        if(grabbedBlock==block2.Id):
                            dist+=4 
                        else:
                            dist+=6
                    else:
                        dist+=5
                elif(dist==3):
                    dist=8
                    if(grabbedBlock!=None):
                        if(grabbedBlock==block2.Id):
                            dist+=5 
                        else:
                            dist+=7
                    else:
                        dist+=6
                else:
                    dist*=2+8
                    
                processed.append(b)

            else:
                dist=max(abs(int(block1.coords[0])-int(block2.coords[0])),abs(int(block1.coords[1])-int(block2.coords[1])),abs(int(block1.coords[2])-int(block2.coords[2]))+1)

                if(grabbedBlock!=None):
                    if(grabbedBlock==block1.Id):
                        dist+=1 
                    else:
                        dist+=3
                else:
                    dist+=2


            if(int(block1.coords[0])==int(block2.coords[0]) and int(block1.coords[1])==int(block2.coords[1]) and int(block1.coords[2])-int(block2.coords[2])==1):
                        return 0, wildcards


            #block1=next((x for x in blockList if x.Id == a), None)
            for bl in blockList:
                if(bl.Id==block1.Id):
                    continue
                if(bl.Id in processed):
                    continue
                if(int(block1.coords[0])==int(bl.coords[0]) and int(block1.coords[1])==int(bl.coords[1]) and int(block1.coords[2])<int(bl.coords[2])):
                    dist+=3
                    if(grabbedBlock==bl.Id):
                        dist-=1
                        
            if(dist<minDist):
                minDist=dist
                if("wildcard" in b1):
                    wildcards[b1]=[a]
                    minBlockOntop=a
                if("wildcard" in b2):
                    wildcards[b2]=[b]


    return minDist,wildcards             



def wildcardLocationHeuristic(blockList,wildcards,coords):
    minDist=1000
    #print(wildcards
    if(wildcards==None):
        for block in blockList:
            moves=max(abs(int(block.coords[0])-int(coords[0])),abs(int(block.coords[1])-int(coords[1])),abs(int(block.coords[2])-int(coords[2])))
            if(moves<minDist):
                minDist=moves
    else:
        #print(wildcards)
        for i in wildcards:
            block=next((x for x in blockList if x.Id == i), None)
            moves=max(abs(int(block.coords[0])-int(coords[0])),abs(int(block.coords[1])-int(coords[1])),abs(int(block.coords[2])-int(coords[2])))
            if(moves<minDist):
                minDist=moves
    return minDist

def wildcardLocationCompare(blockList,wildcards,coords):

    minDist=1000
    matched=False
    if(wildcards==None):
        for block in blockList:
            if(int(block.coords[0])-int(coords[0])==0 and int(block.coords[1])-int(coords[1])==0 and int(block.coords[2])-int(coords[2])==0):
                return True
    else:
        for i in wildcards:
            block=next((x for x in blockList if x.Id == i), None)
            if(int(block.coords[0])-int(coords[0])==0 and int(block.coords[1])-int(coords[1])==0 and int(block.coords[2])-int(coords[2])==0):
                return True

    return False




def defineWildcards(blockList, goalProperties):
    
    wildcardColors=[]
    wildcardDefinitions={} 
    for w in goalProperties:
        if(("color" in w) and ("wildcard" in w)):
            wildcardColors.append(w)
    for w in wildcardColors:
        color=w.split()[3]
        wildcardDefinitions[w.split()[1]]=[]
        for b in blockList:
            if(color in b.props):
                
                wildcardDefinitions[w.split()[1]].append(b.Id)
    return wildcardDefinitions



def compare_coordinates(current, goalState,goalProperties,wildcards):
    if(current.grabbed==True):
        return False

    for block,goal in zip(current.blockList, goalState.blockList):
        if(goal.coords==()):
            continue
        if(int(goal.coords[0])!=int(block.coords[0]) or int(goal.coords[1])!=int(block.coords[1]) or int(goal.coords[2])!=int(block.coords[2])):
            return False

    return True



def compare_relationships2(current, goalState,goalProperties,wildcards):
    for goal in goalProperties:
        g= goal.split()
        if(g[3]=='side-by-side'):
            if(not sideBySideCompare(current.blockList,wildcards,g[1],g[2])):
                return False

        if(g[2]=='location' and "wildcard" in g[1]):
                x1=wildcardLocationHeuristic(current.blockList,wildcards[g[1]] if g[1] in wildcards else None,(g[3],g[4],g[5]))
                if(x1==0):
                    filledWildcard=next((x for x in current.blockList if x.coords == (int(g[3]),int(g[4]),int(g[5]))), None)
                    if(filledWildcard!=None):
                        wildcards[g[1]]=[]
                        wildcards[g[1]].append(filledWildcard.Id)

            
                if(not wildcardLocationCompare(current.blockList,wildcards[g[1]] if g[1] in wildcards else None,(g[3],g[4],g[5]))):
                    return False


        if(g[3]=='on-top-of'):
            if(not onTopCompare(current.blockList,wildcards,g[1],g[2])):
                return False


    return True


def compare_relationships(current, goalState,goalProperties,wildcards):
    for goal in goalProperties:
        g= goal.split()
        if(g[3]=='side-by-side'):
            if(not sideBySideCompare(current.blockList,wildcards,g[1],g[2])):
                return False

        if(g[2]=='location' and "wildcard" in g[1]):
                x1=wildcardLocationHeuristic(current.blockList,wildcards[g[1]] if g[1] in wildcards else None,(g[3],g[4],g[5]))
                if(x1==0):
                    filledWildcard=next((x for x in current.blockList if x.coords == (int(g[3]),int(g[4]),int(g[5]))), None)
                    if(filledWildcard!=None):
                        wildcards[g[1]]=[]
                        wildcards[g[1]].append(filledWildcard.Id)
            
                if(not wildcardLocationCompare(current.blockList,wildcards[g[1]] if g[1] in wildcards else None,(g[3],g[4],g[5]))):
                    return False


        if(g[3]=='on-top-of'):
            if(onTopCompare_debug(current.blockList,wildcards,g[1],g[2])==False):
                return False
            else:
                wildcards=onTopCompare_debug(current.blockList,wildcards,g[1],g[2])


    return True


def compare_relationships_debug(current, goalState,goalProperties,wildcards):
    goalProperties.sort()
    for goal in goalProperties:
        g= goal.split()
        if(g[3]=='side-by-side'):
            if(not sideBySideCompare(current.blockList,wildcards,g[1],g[2])):
                print('here1')
                return False

        if(g[2]=='location' and "wildcard" in g[1]):
                x1=wildcardLocationHeuristic(current.blockList,wildcards[g[1]] if g[1] in wildcards else None,(g[3],g[4],g[5]))
                if(x1==0):
                    filledWildcard=next((x for x in current.blockList if x.coords == (int(g[3]),int(g[4]),int(g[5]))), None)
                    if(filledWildcard!=None):
                        wildcards[g[1]]=[]
                        wildcards[g[1]].append(filledWildcard.Id)
            
                if(not wildcardLocationCompare(current.blockList,wildcards[g[1]] if g[1] in wildcards else None,(g[3],g[4],g[5]))):
                    return False


        if(g[3]=='on-top-of'):
            if(onTopCompare_debug2(current.blockList,wildcards,g[1],g[2])==False):
                #print('here2')
                #print(g[1])
                #print(g[2])
                return False
            else:
                wildcards=onTopCompare_debug(current.blockList,wildcards,g[1],g[2])


    return True

def onTopCompare_debug(blockList,wildcards,b1,b2):
    valid1=[]
    valid2=[]
    if("wildcard" in b1):
        if(b1 in wildcards.keys()):
            valid1.extend(wildcards[b1])
        else:
            for i in blockList:
                valid1.append(i.Id)
    else:
        valid1.append(b1)

    if("wildcard" in b2):
        if(b2 in wildcards.keys()):
            valid2.extend(wildcards[b2])
        else:
            for i in blockList:
                valid2.append(i.Id)
    else:
        valid2.append(b2)

    for a in valid1:
        for b in valid2:
            if(a==b):
                continue

            block1=next((x for x in blockList if x.Id == a), None)
            block2=next((x for x in blockList if x.Id == b), None)
            if(abs(int(block1.coords[0])-int(block2.coords[0]) )==0 and  abs(int(block1.coords[1])-int(block2.coords[1]))==0):
                if(int(block1.coords[2])-int(block2.coords[2])==1):
                    if("wildcard" in b1):
                        wildcards[b1]=[a]
                    if("wildcard" in b2):
                        wildcards[b2]=[b]

                    return wildcards
    return False



def onTopCompare_debug2(blockList,wildcards,b1,b2):
    valid1=[]
    valid2=[]
    if("wildcard" in b1):
        if(b1 in wildcards.keys()):
            valid1.extend(wildcards[b1])
        else:
            for i in blockList:
                valid1.append(i.Id)
    else:
        valid1.append(b1)

    if("wildcard" in b2):
        if(b2 in wildcards.keys()):
            valid2.extend(wildcards[b2])
        else:
            for i in blockList:
                valid2.append(i.Id)
    else:
        valid2.append(b2)

    for a in valid1:
        for b in valid2:
            if(a==b):
                continue

            block1=next((x for x in blockList if x.Id == a), None)
            block2=next((x for x in blockList if x.Id == b), None)
            if(abs(int(block1.coords[0])-int(block2.coords[0]) )==0 and  abs(int(block1.coords[1])-int(block2.coords[1]))==0):
                if(int(block1.coords[2])-int(block2.coords[2])==1):
                    #print(block1.coords)
                    #print(block2.coords)
                    #print(int(block1.coords[2])-int(block2.coords[2]))
                    #sys.exit()
                    if("wildcard" in b1):
                        wildcards[b1]=[a]
                    if("wildcard" in b2):
                        wildcards[b2]=[b]

                    return wildcards
    return False

def compareCoords(blockCoords, goalCoords):
    if(goalCoords==()):
        return True
    else:
        return (int(blockCoords[0])==int(goalCoords[0]) and int(blockCoords[1])==int(goalCoords[1]) and int(blockCoords[2])==int(goalCoords[2]))
