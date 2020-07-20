import socket, pickle
import random
import multiprocessing
import threading
import datetime
from datetime import timedelta

nodesNumber = 2
neighborsNumber = 1
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

    def sendHelloPacket(self, nodePort, lastSendTime, lastRecieveTime):
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        message = HelloPacket(self.id, self.ip, self.port, "?", self.neighbors, lastSendTime, lastRecieveTime)
        data = pickle.dumps(message)
        UDPClientSocket.sendto(data, (nodesIp, nodePort))
        print("I(" + str(self.port) + ") sent hello packet to " + str(nodePort))

    def sayHelloToNeighbors(self):
        for neighborInfo in self.neighbors:
            print('3')
            now = datetime.datetime.now()
            self.sendHelloPacket(neighborInfo[0], now, neighborInfo[2])
            neighborInfo = (neighborInfo[0], now, neighborInfo[2])
  
    def sayHelloToNodeSaidHello(self):
        print('2')
        nodeInfo = random.choice(self.nodesSaidHelloToMe)
        now = datetime.datetime.now()
        self.sendHelloPacket(nodeInfo[0], now, nodeInfo[2])
        newNodeInfo = (nodeInfo[0], now, nodeInfo[2])
        self.nodesSaidHelloToMe.remove(nodeInfo)
        self.nodesIsaidHelloToThem.append(newNodeInfo)

    def sayHelloToOtherNode(self):
        print('1')
        nodePort = random.choice(self.others)
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

def getPortNumbers():
    ports = []
    for i in range(nodesNumber):
        ports.append(random.randint(5000,10000))
    return ports
    
def createNewNode(nodesRunningStatus, id, ports):
    print("----")
    print(nodesRunningStatus[id])
    nodePort = ports[i]
    del ports[i]
    node = Node(id, nodesIp, nodePort, ports)
    node.run(nodesRunningStatus)


if __name__ == '__main__':
    ports = getPortNumbers()
    nodesRunningStatus = multiprocessing.Manager().list()
    for i in range(nodesNumber):
        nodesRunningStatus.append(True)

    for i in range(nodesNumber):
        p = multiprocessing.Process(target=createNewNode, args=(nodesRunningStatus, i, ports, ))
        p.start()
    # for i in range(nodesNumber):
    #     nodesRunningStatus[i] = False
    
    p.join()
    
    