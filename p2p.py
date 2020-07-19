import socket, pickle
import random
import multiprocessing

class HelloPacket:
    def __init__(self, id, ip, port, packetType, neighbors, lastSendedAt, lastRecievedAt):
        self.senderId = id
        self.senderIp = ip
        self.senderPort = port
        self.packetType = packetType #what is type?
        self.neighbors = neighbors
        self.lastSendedAt = lastSendedAt
        self.lastRecievedAt = lastRecievedAt

def createNodes(nodesNumber):
    nodes = []
    for i in range(nodesNumber):
        nodePort = random.randint(5000,10000)
        nodeIp = "127.0.0.1"
        nodes.append((nodeIp,nodePort)) #all nodes considered to exist on local host
    print("Nodes created")
    return nodes

def response(nodes, nodeIndex):
    nodeIp = nodes[nodeIndex][0]
    nodePort = nodes[nodeIndex][1]
    UDPServerSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDPServerSocket.bind((nodeIp, nodePort))
    while(True):
        data, address = UDPServerSocket.recvfrom(1024)
        message = pickle.loads(data)
        print("Hello Message From: (", message.senderIp ,",", message.senderPort, ") To: ", nodes[nodeIndex])
        # serverSocket.sendto(bytesToSend, address)

def findNeighbors(nodes, nodeIndex):
    nodeNeighbors = []
    availableNodes = [x for x in range(nodesNumber) if x!=nodeIndex]
    # while(len(nodeNeighbors)<3):
    neighborIndex = random.choice(availableNodes)
    print("client ", nodes[nodeIndex], " sent message to ", nodes[neighborIndex])
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    nodeIp = nodes[nodeIndex][0]
    nodePort = nodes[nodeIndex][1]
    message = HelloPacket(nodeIndex, nodeIp, nodePort, "?", nodeNeighbors, 0,0)
    data = pickle.dumps(message)
    UDPClientSocket.sendto(data, nodes[neighborIndex])



nodesNumber = 6
neighborsNumber = 3
if __name__ == '__main__':
    nodes = createNodes(nodesNumber)
    jobs = []
    for i in range(nodesNumber):
        p = multiprocessing.Process(target=response, args=(nodes,i,))
        jobs.append(p)
        p.start()
    for i in range(nodesNumber):
        p = multiprocessing.Process(target=findNeighbors, args=(nodes,i,))
        jobs.append(p)
        p.start()