import os
import xml.etree.ElementTree as ET
from tkinter import Tk
from tkinter.filedialog import askopenfilename

class Chip:
    def __init__(self, hdlName, width, height, id):
        self.hdlName = hdlName
        self.width = width
        self.height = height
        self.id = id
    def __str__(self):
        return "Chip: [name: %s, id: %d]" % (self.hdlName, self.id)

class Node:
    traversed = False
    parsed = False
    depth = 0
    def __init__(self, label, chipId, outputId, numInputs, x, y):
        self.label = label
        self.chipId = chipId
        self.outputId = outputId
        self.numInputs = numInputs
        self.x = x
        self.y = y
    def __str__(self):
        return "Node: [label: %s, chipId: %d, outputId: %d, inputs: %d, depth: %d, x: %d, y: %d]" % (self.label, self.chipId, self.outputId, self.numInputs, self.depth, self.x, self.y)

class Wire:
    def __init__(self, fromX, fromY, toX, toY, id):
            self.fromX = fromX
            self.fromY = fromY
            self.toX = toX
            self.toY = toY
            self.id = id

class Connection:
    def __init__(self, fromId, toId, inputId):
        self.fromId = fromId
        self.toId = toId
        self.inputId = inputId
    def __str__(self):
        return "Connection: [fromId: %d, toId: %d, inputId: %d]" % (self.fromId, self.toId, self.inputId)

nodes = []
inputNodes = []
outputNodes = []
wires = []
chips = []
connections = []
outputConnections = []
inputConnections = []

# Chip Dictionary
chips.append(Chip("Input", 0, 0, 0))
chips.append(Chip("Output", 0, 0, 1))
chips.append(Chip("And", 50, 40, 2))
chips.append(Chip("Or", 50, 40, 3))
chips.append(Chip("Not", 30, 10, 4))
chips.append(Chip("Nand", 60, 40, 5))
chips.append(Chip("Xor", 60, 40, 6))
chips.append(Chip("Nor", 60, 40, 7))
chips.append(Chip("Xnor", 70, 40, 8))
#-----------------------

Tk().withdraw()
#filename = "C:\\Users\\Evan\\Desktop\\Micro\\logism\\AndTest.circ"
filename = askopenfilename()
xmlTree = ET.parse(filename)
xmlRoot = xmlTree.getroot()
circuitRoot = xmlRoot.find("circuit")

wireList = circuitRoot.findall("wire")
inputList = circuitRoot.findall("comp[@name='Pin']/a[@name='tristate']/..")
outputList = circuitRoot.findall("comp[@name='Pin']/a[@name='output']/..")
gateList = circuitRoot.findall("comp/a[@name='inputs']/..")
gateList.extend(circuitRoot.findall("comp[@name='NOT Gate']")) # no input tag so must be searched for separately

def parseLocationString(locationString):
    locStr = locationString.replace("(", "").replace(")", "")
    location = locStr.split(",")
    return [int(location[0]), int(location[1])]

def parseLabel(gateNode):
    labelNode = gateNode.find("a[@name='label']")
    if labelNode == None:
        return ""
    else:
        return labelNode.attrib["val"]


# parse wire data
currentWireId = 0
for wire in wireList:
    fromPos = parseLocationString(wire.attrib["from"])
    toPos = parseLocationString(wire.attrib["to"])
    wires.append(Wire(fromPos[0], fromPos[1], toPos[0], toPos[1], currentWireId))
    currentWireId += 1

# create unique nodes for each gate
currentOutputId = 0
for gate in gateList:
    # parse the chip
    chipId = -1
    for chip in chips:
        if chip.hdlName.lower() == gate.attrib["name"].split(" ")[0].lower():
            chipId = chip.id
            break

    # parse location
    location = parseLocationString(gate.attrib["loc"])

    # parse label
    label = parseLabel(gate)

    # parse inputs
    numInputs = 0
    inputElem = gate.find("a[@name='inputs']")
    if inputElem != None:
        numInputs = int(inputElem.attrib["val"])
    else:
        numInputs = 1
    
    nodes.append(Node(label, chipId, currentOutputId, numInputs, location[0], location[1]))
    currentOutputId += 1

# create input nodes
for _input in inputList:
    location = parseLocationString(_input.attrib["loc"])
    label = parseLabel(_input)
    inputNodes.append(Node(label, 0, currentOutputId, 0, location[0], location[1]))
    currentOutputId += 1

# create output nodes
for _output in outputList:
    location = parseLocationString(_output.attrib["loc"])
    label = parseLabel(_output)
    outputNodes.append(Node(label, 0, currentOutputId, 0, location[0], location[1]))
    currentOutputId += 1

# traverse wire chain until we get the position of the end of a wire
def traverseWires(wireStartPos, wireId, endingPositions):
    added = False
    for wire in wires:
        if not(wireId == wire.id):
            if wire.fromX == wireStartPos[0] and wire.fromY == wireStartPos[1]:
                added = True
                traverseWires([wire.toX, wire.toY], wire.id, endingPositions)
            if wire.toX == wireStartPos[0] and wire.toY == wireStartPos[1]:
                added = True
                traverseWires([wire.fromX, wire.fromY], wire.id, endingPositions)

    if not added:
        endingPositions.append(wireStartPos)

# sorting function key definition
def getSecondVal(val):
    return val[1]

# create the connections between the position of a starting node and any nodes connected to its output
def createConnections(fromNode, currentDepth, isInput):
    if fromNode.depth < currentDepth:
        fromNode.depth = currentDepth
    if not fromNode.traversed:
        inputPositions = []
        traverseWires([fromNode.x, fromNode.y], -1, inputPositions)

        # find the node we are inputting to
        for node in nodes:
            if node.outputId != fromNode.outputId:
                inputChip = None
                for chip in chips:
                    if chip.id == node.chipId:
                        inputChip = chip
                if not (inputChip == None):
                    inputX = node.x - inputChip.width # assumes all gates have their inputs lined up on the y-axis
                    topInputPos = 0 # we can find this because we know all inputs are separated by a y value of 10
                    evenInputs = node.numInputs % 2 == 0

                    if node.numInputs > int(inputChip.height / 10): # only do this if the inputs are bigger than the chip iteself
                        if evenInputs: # if even num of inputs, there is a gap between inputs at output y
                            topInputPos = node.y - int(10 * node.numInputs * 0.5)
                        else:
                            topInputPos = node.y - int(10 * (node.numInputs - 1) * 0.5)
                    else:
                        topInputPos = node.y + int(inputChip.height * 0.5)

                    nodeInputPositions = []
                    currentPosition = topInputPos
                    if node.numInputs > 3: # 1-3 inputs are special cases
                        for i in range(node.numInputs):
                            if evenInputs and i == int(node.numInputs * 0.5):
                                currentPosition += 10
                            nodeInputPositions.append([inputX, currentPosition])
                            currentPosition += 10
                    else:
                        if node.numInputs == 1: # input y = output y
                            nodeInputPositions.append([inputX, node.y])
                        elif node.numInputs == 2: # top and bottom
                            nodeInputPositions.append([inputX, topInputPos])
                            nodeInputPositions.append([inputX, node.y + (node.y - topInputPos)])
                        else: # top middle and bottom
                            nodeInputPositions.append([inputX, topInputPos])
                            nodeInputPositions.append([inputX, node.y])
                            nodeInputPositions.append([inputX, node.y + (node.y - topInputPos)])

                    nodeInputPositions.sort(key=getSecondVal) # sort by y value. this assumes all gates have their inputs lined up on the y-axis.

                    inputIndex = 0
                    hasConnection = False
                    for pos in nodeInputPositions:
                        if pos in inputPositions:
                            hasConnection = True
                            if isInput:
                                inputConnections.append(Connection(fromNode.outputId, node.outputId, inputIndex))
                            else:
                                connections.append(Connection(fromNode.outputId, node.outputId, inputIndex))
                        inputIndex += 1

                    if hasConnection:
                        fromNode.traversed = True
                        createConnections(node, currentDepth + 1, False)
            

        # check for any output connections
        for node in outputNodes:
            for pos in inputPositions:
                if pos == [node.x, node.y]:
                    outputConnections.append(Connection(fromNode.outputId, node.outputId, 0))

        fromNode.traversed = True

def findNode(nodeId, nodeArray):
    for node in nodeArray:
        if nodeId == node.outputId:
            return node
    return None


finalOutput = ""
def buildHdl(outputNode): # furthest node in the calculation chain
    global finalOutput
    if not (outputNode == None) and not outputNode.parsed:
        output = ""
        chipData = None

        if outputNode.chipId != 0:
            for chip in chips:
                if chip.id == outputNode.chipId:
                    chipData = chip

        if not (chipData == None):
            output = chipData.hdlName + "("

        for connection in connections:
            if connection.toId == outputNode.outputId:
                outputNode.parsed = True
                buildHdl(findNode(connection.fromId, nodes))
                if chipData != None:
                    output += chr(ord('a') + connection.inputId) + "=output" + str(connection.fromId) + ","

        if chipData != None:
            for _input in inputConnections: # check for input connections (not great)
                if _input.toId == outputNode.outputId:
                    node = findNode(_input.fromId, inputNodes)
                    output += chr(ord('a') + _input.inputId)
                    if not (node == None) and not (node.label == ""):
                        output += "=" + node.label + ","
                    else:
                        output += "=in[" + str(_input.toId) + "],"

        foundOutput = False
        for _output in outputConnections: # check for output connections
            if _output.toId == outputNode.outputId:
                node = findNode(_output.fromId, nodes)
                outputNode.parsed = True
                buildHdl(node)
            elif _output.fromId == outputNode.outputId:
                node = findNode(_output.toId, outputNodes)
                if not (node.label == ""):
                    output += "out=" + node.label
                else:
                    output += "out=out[" + str(_output.toId) + "]"
                foundOutput = True
            break
        if chipData != None:
            if not foundOutput:
                output += "out=output" + str(outputNode.outputId)
            output += ");\n"
        outputNode.parsed = True
        finalOutput += output;
    
for node in inputNodes:
    createConnections(node, 0, True)

for node in outputNodes:
    buildHdl(node)

print("HDL Output:\n")
print(finalOutput)