import socket, pickle
import random
import multiprocessing
import threading
import datetime
from datetime import timedelta
import sys
import sched, time
import signal
import os
import json

nodesNumber = 6
neighborsNumber = 3
nodesIp = '127.0.0.1'


class HelloPacket:
    def __init__(self, id, ip, port, packetType, neighbors, lastSendedAt, lastRecievedAt):
        self.senderId = id
        self.senderIp = ip
        self.senderPort = port
        self.packetType = packetType
        self.neighbors = neighbors 
        self.lastSendedAt = lastSendedAt
        self.lastRecievedAt = lastRecievedAt


class Node:
    def __init__(self, id, ip, port, others):
        self.id = id
        self.ip = ip
        self.port = port
        self.others = others
        self.neighbors = [] #[(port, lastSendTime, lastRecieveTime)]
        self.nodesSaidHelloToMe = []
        self.nodesIsaidHelloToThem = []
        self.neighborsHistory = {} #{port: [numberOfNeighberhoodVisits , sendedPackets, recievedPackets, neighbors]}

    def sendHelloPacket(self, nodePort, lastSendTime, lastRecieveTime):
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        message = HelloPacket(self.id, self.ip, self.port, "?", self.neighbors, lastSendTime, lastRecieveTime)
        data = pickle.dumps(message)
        possiblity = random.randint(1,100)
        UDPClientSocket.sendto(data, (nodesIp, nodePort))

    def sayHelloToNeighbors(self):
        for i in range(len(self.neighbors)):
            # print("1 - sayHelloToNeighbors from " + str(self.port))
            now = datetime.datetime.now()
            # print(str(self.port) + " sent hello packet to neighbor :" + str(self.neighbors[i][0]) + " at " + str(now))
            self.sendHelloPacket(self.neighbors[i][0], now, self.neighbors[i][2])
            self.neighbors[i] = (self.neighbors[i][0], now, self.neighbors[i][2])
            self.updateNeighborsHistory(self.neighbors[i][0],packetIsRecieved= False, packetIsSended=True, isNeighborNow=True, nodesNeighbors=[])
  
    def sayHelloToNodeSaidHello(self):
        nodeIndex = random.randint(0, len(self.nodesSaidHelloToMe)-1)
        nodeInfo = self.nodesSaidHelloToMe[nodeIndex]
        # print("2 - sayHelloToNodeSaidHello from " + str(self.port))
        now = datetime.datetime.now()
        self.sendHelloPacket(nodeInfo[0], now, nodeInfo[2])
        newNodeInfo = (nodeInfo[0], now, nodeInfo[2])
        
        del self.nodesSaidHelloToMe[nodeIndex]
        self.nodesIsaidHelloToThem.append(newNodeInfo)

    def sayHelloToOtherNode(self):
        neighborsPorts = [neighbor[0] for neighbor in self.neighbors]
        availablePorts = [port for port in self.others if port not in neighborsPorts]
        if(len(availablePorts)>0):
            # print("3 - sayHelloToOtherNode from " + str(self.port))
            nodePort = random.choice(availablePorts)
            now = datetime.datetime.now()
            self.sendHelloPacket(nodePort, now, datetime.datetime.min)
            newNodeInfo = (nodePort, now, datetime.datetime.min)
            self.nodesIsaidHelloToThem.append(newNodeInfo)

    def sayHello(self, runningStatus):
        threading.Timer(2.0, self.sayHello, args = (runningStatus,)).start()
        if runningStatus[self.id] :
            self.sayHelloToNeighbors()

        
    def findNeighbors(self, runningStatus):
        if runningStatus[self.id] :
            if len(self.neighbors) < neighborsNumber:
                if len(self.nodesSaidHelloToMe) > 0:
                    self.sayHelloToNodeSaidHello()
                else:
                    self.sayHelloToOtherNode()

    def handleRecievedMessages(self, message):
        nodePort = message.senderPort
        for i in range(len(self.neighbors)) :
            if self.neighbors[i][0] == nodePort:
                print("5 - recieve massage from my neighbor i am " + str(self.port))
                self.neighbors[i] =  (self.neighbors[i][0], self.neighbors[i][1], message.lastSendedAt)
                self.updateNeighborsHistory(nodePort,packetIsRecieved= True, packetIsSended=False, isNeighborNow=True, nodesNeighbors=message.neighbors)
                return
        for i in range(len(self.nodesIsaidHelloToThem)):
            if self.nodesIsaidHelloToThem[i][0] == nodePort:
                print("6 - recieve massage from nodesIsaidHelloToThem i am " + str(self.port))
                if len(self.neighbors) < neighborsNumber:
                    newNodeInfo = (self.nodesIsaidHelloToThem[i][0], self.nodesIsaidHelloToThem[i][1], message.lastSendedAt)
                    self.neighbors.append(newNodeInfo)
                    self.updateNeighborsHistory(nodePort,packetIsRecieved= True, packetIsSended=False, isNeighborNow=False, nodesNeighbors=message.neighbors)
                    del self.nodesIsaidHelloToThem[i]
                else:
                    self.nodesIsaidHelloToThem[i] = (self.nodesIsaidHelloToThem[i][0], self.nodesIsaidHelloToThem[i][1], message.lastSendedAt)
                return
        for i in range(len(self.nodesSaidHelloToMe)):
            if self.nodesSaidHelloToMe[i][0] == nodePort:
                print("7 - recieve massage from nodesSaidHelloToMe i am " + str(self.port))
                self.nodesSaidHelloToMe[i] = (self.nodesSaidHelloToMe[i][0], self.nodesSaidHelloToMe[i][1], message.lastSendedAt)
                return

        newNodeInfo = (nodePort, datetime.datetime.min, message.lastSendedAt)
        print("8 - recieve massage from others i am " + str(self.port))
        self.nodesSaidHelloToMe.append(newNodeInfo)    

    def listen(self, runningStatus):
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDPServerSocket.bind((self.ip, self.port))
        while(True):
            if runningStatus[self.id] :
                if(not packetIsLost()):
                    data, address = UDPServerSocket.recvfrom(1024)
                    message = pickle.loads(data)
                    self.handleRecievedMessages(message)
        
    def checkNeighbors(self, runningStatus):
        if runningStatus[self.id] :
            for neighborInfo in self.neighbors:
                expireDate = neighborInfo[2] + timedelta(seconds = 8) 
                now = datetime.datetime.now()   
                if now > expireDate :
                    print("4 - checkNeighbors in " + str(self.port))
                    # print("now : " + str(now) + " in " + str(self.port))
                    # print("last time : " + str(neighborInfo[2]) + " in " + str(self.port))
                    # print("expire : " + str(expireDate) + " in " + str(self.port))
                    self.neighbors.remove(neighborInfo)
    
    def updateNeighborsHistory(self,neighborPort, packetIsRecieved, packetIsSended, isNeighborNow, nodesNeighbors):
        if(packetIsRecieved):
            if(neighborPort in self.neighborsHistory):
                if(not isNeighborNow):
                    self.neighborsHistory[neighborPort][0] += 1
                else:
                    self.neighborsHistory[neighborPort][2] += 1
                    self.neighborsHistory[neighborPort][3] = nodesNeighbors
            else:
                self.neighborsHistory.update({neighborPort: [1,0,0,nodesNeighbors]})
        elif(packetIsSended):
            self.neighborsHistory[neighborPort][1] += 1

    def run(self, nodesRunningStatus):
        curID = threading.currentThread().ident
        listeningThread = threading.Thread(target=self.listen, args=(nodesRunningStatus,))
        endTime = datetime.datetime.now() + timedelta(seconds = 10)

        self.sayHello(nodesRunningStatus)
        listeningThread.start()

        if(threading.currentThread().ident == curID):
            while(True):
                if(datetime.datetime.now() > endTime):
                    self.reportNetworkTopology()
                    self.reportNeighborsStatus()
                    self.reportCurrentNeighbors()
                    break
                else:
                    if len(self.neighbors) < neighborsNumber:
                        self.findNeighbors(nodesRunningStatus)
                        self.checkNeighbors(nodesRunningStatus)


        

    def writeInFile(self, fileName, fileData):
        f = open(fileName,"w")
        f.write(fileData)
        f.close()

    def reportNetworkTopology(self):
        topology = "Reporter Port is : " + str(self.port) + "\n"
        topology += str(self.port) + "\n"
        for neighbor in self.neighbors :
            topology += "     <--> " + str(neighbor[0]) + "\n"
            neighborsOfNeighbor = self.neighborsHistory[neighbor[0]][3]
            for neighborOfNeighbor in neighborsOfNeighbor:
                if(neighborOfNeighbor[0] != self.port):
                    topology += "               <--> " + str(neighborOfNeighbor[0]) + "\n"

        self.writeInFile("node_"+str(self.id)+"_4.txt", topology)
        
        
    def reportNeighborsStatus(self):
        neighborsJsonList = []
        neighborsPorts = self.neighborsHistory.keys()
        for port in neighborsPorts:
            neighborsJsonList.append({ 
                            "neighborIp" : nodesIp,
                            "neighborPort" : port,
                            "neighborhoodNumber": self.neighborsHistory[port][0],
                            "sendedPacketsNumber": self.neighborsHistory[port][1],
                            "recievedPacketsNumber": self.neighborsHistory[port][0]
                             })
        x = {
            "nodeIp": nodesIp,
            "nodePort": self.port,
            "neighborsHistory": neighborsJsonList
        }
        filename = "node_"+str(self.id)+"_1.txt"
        self.writeInFile(filename, json.dumps(x))

    def reportCurrentNeighbors(self):
        neighborsJsonList = []
        for neighbor in self.neighbors:
            neighborsJsonList.append({
                "neighborIp" : nodesIp,
                "neighborPort" : neighbor[0],
                "lastSendAt" : str(neighbor[1]),
                "lastRecievedAt" : str(neighbor[2])
            })
        x = {
            "nodeIp": nodesIp,
            "nodePort": self.port,
            "currentNeighbors": neighborsJsonList
        }
        filename = "node_"+str(self.id)+"_2.txt"
        self.writeInFile(filename, json.dumps(x))



def packetIsLost():
    randomNumber = random.randint(1,100)
    if(randomNumber > 5):
        return False
    return True

def getPortNumbers():
    ports = []
    for i in range(nodesNumber):
        ports.append(random.randint(5000,10000))
    return ports

def createNetworkNodes(ports):
    nodes = []
    for i in range(nodesNumber):
        nodePort = ports[i]
        others = [port for j,port in enumerate(ports) if j!=i]
        node = Node(i, nodesIp, nodePort, others)
        nodes.append(node)
    return nodes

def setNodesRunningStatus(nodesRunningStatus, firstOffNode, secondOffNode):
    print("first : " + str(firstOffNode))
    print("second : " + str(secondOffNode))
    if firstOffNode == -1 and secondOffNode == -1:
        onNodes = [x for x in range(nodesNumber)]
        nodeId = random.choice(onNodes)
        firstOffNode = nodeId
        nodesRunningStatus[firstOffNode] = False
    elif secondOffNode == -1:
        onNodes = [x for x in range(nodesNumber) if x != firstOffNode]
        nodeId = random.choice(onNodes)
        secondOffNode = nodeId
        nodesRunningStatus[secondOffNode] = False
    else:
        nodesRunningStatus[firstOffNode] = True
        onNodes = [x for x in range(nodesNumber) if x != secondOffNode]
        nodeId = random.choice(onNodes)
        firstOffNode = secondOffNode
        secondOffNode = nodeId
        nodesRunningStatus[secondOffNode] = False
    t1 = threading.Timer(10.0, setNodesRunningStatus, args = (nodesRunningStatus,firstOffNode,secondOffNode,))
    t1.setName('timer')
    t1.start()

if __name__ == '__main__':
    ports = getPortNumbers()
    nodes = createNetworkNodes(ports)
    nodesRunningStatus = multiprocessing.Manager().list()
    for i in range(nodesNumber):
        nodesRunningStatus.append(True)
    
    setNodesRunningStatus(nodesRunningStatus, -1, -1)

    jobs = []
    for i in range(nodesNumber):
        p = multiprocessing.Process(target=nodes[i].run, args=(nodesRunningStatus, ))
        jobs.append(p)
        p.start()
    p.join()
