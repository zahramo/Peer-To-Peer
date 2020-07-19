import socket, pickle
import random
import multiprocessing
import threading

nodesNumber = 6
neighborsNumber = 3

class HelloPacket:
    def __init__(self, id, ip, port, packetType, neighbors, lastSendedAt, lastRecievedAt):
        self.senderId = id
        self.senderIp = ip
        self.senderPort = port
        self.packetType = packetType #what is type?
        self.neighbors = neighbors
        self.lastSendedAt = lastSendedAt
        self.lastRecievedAt = lastRecievedAt

class Node:
    def __init__(self, id, ip, port, others):
        self.id = id
        self.ip = ip
        self.port = port
        self.others = others
        self.neighbors = []
    def findNeighbors(self):
        print('find neighbors')
    def sayHello(self):
        print('say hello')
    def listen(self):
        UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        UDPServerSocket.bind((self.ip, self.port))
        while(True):
            data, address = UDPServerSocket.recvfrom(1024)
            message = pickle.loads(data)
        
    def run(self):    
        t1 = threading.Thread(target=self.findNeighbors, args=())
        t2 = threading.Thread(target=self.sayHello, args=())
        # t3 = threading.Thread(target=self.listen, args=())
        t1.start()
        t2.start()
        # t3.start()

def getPortNumbers():
    ports = []
    for i in range(nodesNumber):
        ports.append(random.randint(5000,10000))
    return ports
    
def createNewNode(id, ports):
    nodePort = ports[i]
    del ports[i]
    nodeIp = '127.0.0.1'
    node = Node(id, nodeIp, nodePort, ports)
    node.run()


if __name__ == '__main__':
    ports = getPortNumbers()
    for i in range(nodesNumber):
        p = multiprocessing.Process(target=createNewNode, args=(i, ports))
        p.start()