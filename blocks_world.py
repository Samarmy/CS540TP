'''
Block class keeps information about each block: which blocks are beside it, which block its on top of, and its height.
Node class keeps information about the cost, heuristic value, and parent node. 
'''

class Block:
  onTopOf=None
  Id=None
  height=0
  props=None
  coords=None
  def __init__(self, Id):
    self.Id=Id
    self.sides=[]
    self.onTopOf=None
    self.props=[]
    self.coords=()
    
  def addSide(self,block):
      self.sides.append(block)

  def clearSides(self):
      self.sides=[]
  def removeSide(self,block):
      self.sides.remove(block)

  def addLocation(self,x,y,z):
      self.coords=(x,y,z)

  def addProp(self,color):
      self.props.append(color)


class Node:
  action=None
  def __init__(self, blocks,parent,grabbed=False,grabbedBlock=''):
    self.blockList=blocks
    self.f=0
    self.g=0
    self.h=0
    self.parent=parent
    self.grabbed=grabbed
    self.grabbedBlock=grabbedBlock
