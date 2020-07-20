import socket, pickle
import random
import multiprocessing
import threading
import datetime
from datetime import timedelta
import sys
import sched, time

nodesNumber = 6
neighborsNumber = 3
nodesIp = '127.0.0.1'


class HelloPacket:
    def __init__(self, id, ip, port, packetType, neighbors, lastSendedAt, lastRecievedAt):
        self.senderId = id
        self.senderIp = ip
        self.senderPort = port
        self.packetType = packetType
        self.neighbors = neighbors #[(port, lastSendTime, lastRecieveTime)]
        self.lastSendedAt = lastSendedAt
        self.lastRecievedAt = lastRecievedAt


class Node:
    def __init__(self, id, ip, port, others):
        self.id = id
        self.ip = ip
        self.port = port
        self.others = others
        self.neighbors = []
        self.nodesSaidHelloToMe = []
        self.nodesIsaidHelloToThem = []
        print("Node ",id," created on port ",port,". other ports are: ",others)

    def introduce(self):
        print("Im ",self.port,". my neighbors are ",[x[0] for x in self.neighbors],
         " and this people said hello to me: ",[x[0] for x in self.nodesSaidHelloToMe])

    def sendHelloPacket(self, nodePort, lastSendTime, lastRecieveTime):
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        message = HelloPacket(self.id, self.ip, self.port, "?", self.neighbors, lastSendTime, lastRecieveTime)
        data = pickle.dumps(message)
        possiblity = random.randint(1,100)
        UDPClientSocket.sendto(data, (nodesIp, nodePort))
        # time.sleep(15)
        # print("I(" + str(self.port) + ") sent hello packet to " + str(nodePort))

    def sayHelloToNeighbors(self):
        for neighborInfo in self.neighbors:
            self.introduce()
            print("I(" + str(self.port) + ") am sending packet to MY NEIGHBOR: ",neighborInfo[0])
            now = datetime.datetime.now()
            self.sendHelloPacket(neighborInfo[0], now, neighborInfo[2])
            neighborInfo = (neighborInfo[0], now, neighborInfo[2])
  
    def sayHelloToNodeSaidHello(self):
        nodeInfo = random.choice(self.nodesSaidHelloToMe)
        self.introduce()
        print("I(" + str(self.port) + ") am sending packet to HELLO FRIEND: ",nodeInfo[0])
        now = datetime.datetime.now()
        self.sendHelloPacket(nodeInfo[0], now, nodeInfo[2])
        newNodeInfo = (nodeInfo[0], now, nodeInfo[2])
        self.nodesSaidHelloToMe.remove(nodeInfo)
        self.nodesIsaidHelloToThem.append(newNodeInfo)

    def sayHelloToOtherNode(self):
        neighborsPorts = [neighbor[0] for neighbor in self.neighbors]
        availablePorts = [port for port in self.others if port not in neighborsPorts]
        if(len(availablePorts)>0):
            nodePort = random.choice(availablePorts)
            self.introduce()
            print("I(" + str(self.port) + ") am sending packet to STRANGER: ",nodePort)
            now = datetime.datetime.now()
            self.sendHelloPacket(nodePort, now, datetime.datetime.min)
            newNodeInfo = (nodePort, now, datetime.datetime.min)
            self.nodesIsaidHelloToThem.append(newNodeInfo)

    def sayHello(self, runningStatus):
        threading.Timer(2.0, self.sayHello, args = (runningStatus,)).start()
        if runningStatus[self.id] :
            self.sayHelloToNeighbors()

        
    def findNeighbors(self, runningStatus):
        while(True):
            if runningStatus[self.id] :
                if len(self.neighbors) < neighborsNumber:
                    if len(self.nodesSaidHelloToMe) > 0:
                        self.sayHelloToNodeSaidHello()
                    else:
                        self.sayHelloToOtherNode()

    def handleRecievedMessages(self, message):
        nodePort = message.senderPort
        for neighbor in self.neighbors:
            if neighbor[0] == nodePort:
                neighbor =  (neighbor[0], neighbor[1], message.lastSendedAt)
                return
        for node in self.nodesIsaidHelloToThem:
            if node[0] == nodePort:
                if(len(self.neighbors) < neighborsNumber):
                    newNodeInfo = (nodePort, node[1], message.lastSendedAt)
                    self.nodesIsaidHelloToThem.remove(node)
                    self.neighbors.append(newNodeInfo)
                return

        for node in self.nodesSaidHelloToMe:
            node = (node[0], node[1], message.lastSendedAt)
            return
    
        newNodeInfo = (nodePort, datetime.datetime.min, message.lastSendedAt)
        self.nodesSaidHelloToMe.append(newNodeInfo)    

    def listen(self, runningStatus):
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDPServerSocket.bind((self.ip, self.port))
        while(True):
            if runningStatus[self.id] :
                if(not packetIsLost()):
                    data, address = UDPServerSocket.recvfrom(1024)
                    message = pickle.loads(data)
                    print("I(" + str(self.port) + ") recieve hello packet from " + str(message.senderPort))
                    self.handleRecievedMessages(message)
        
    def checkNeighbors(self, runningStatus):
        while(True):
            if runningStatus[self.id] :
                for neighborInfo in self.neighbors:
                    expireDate = neighborInfo[2] + timedelta(seconds = 8)    
                    if datetime.datetime.now() > expireDate :
                        self.neighbors.remove(neighborInfo)

    def run(self, nodesRunningStatus):  
        t1 = threading.Thread(target=self.sayHello, args=(nodesRunningStatus,))
        t2 = threading.Thread(target=self.listen, args=(nodesRunningStatus,))
        t3 = threading.Thread(target=self.findNeighbors, args=(nodesRunningStatus,))
        t4 = threading.Thread(target=self.checkNeighbors, args=(nodesRunningStatus,))
        t1.start()
        t2.start()
        t3.start()
        t4.start()


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

# def turnANodeOff(nodesRunningStatus):
#     nodeId = random.randint(0,nodesNumber-1)
#     f = open(("turnOff"+str(nodeId)+".txt"), "w")
#     f.write("Node "+ str(nodeId)+ " is turning off\n")
#     t_end = time.time() + 20
#     while time.time() < t_end:
#         nodesRunningStatus[nodeId] = False
#         f.write(str(time.time())+'\n')
#     nodesRunningStatus[nodeId] = True
#     f.write("Node "+ str(nodeId) + " turned on\n")
#     f.close()

if __name__ == '__main__':
    ports = getPortNumbers()
    nodes = createNetworkNodes(ports)
    nodesRunningStatus = multiprocessing.Manager().list()
    for i in range(nodesNumber):
        nodesRunningStatus.append(True)

    for i in range(nodesNumber):
        p = multiprocessing.Process(target=nodes[i].run, args=(nodesRunningStatus, ))
        p.start()
    
    # threading.Timer(10.0, turnANodeOff, args = (nodesRunningStatus,)).start()
    
    p.join()
    
    