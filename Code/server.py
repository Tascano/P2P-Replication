"""----------------------------------------------------------------------------------------------------------
A Simple Peer to Peer File System
-Ambrose Tuscano, Jayalakshmi

Server1: 
IP: 192.168.0.123

next Server connections = ['192.168.0.111', 9999], ['192.168.0.113', 9999], ['192.168.0.137', 9999] 


Changes: 1. Current server is bind to directly with the localhost. 
         2. Consider changing values of the servers to connect to 

----------------------------------------------------------------------------------------------------------"""


#------------------> Imports <------------------------------

import socket
import os
import threading
import queue
import time
from random import randint

#------------------> Functions <------------------------------
#function to check if server is already connected(helps since we iterate through servers at start)
def ConnectedIPs(ips, serverslist):                            
    isConnected = len([item for item in serverslist if ips[0] == ips[0]])
    if isConnected > 0:
        return True
    else:
        return False

#manage disconnection of server here
def ServerDisconnection(conn, PeerSystemsConnected):
    for item in PeerSystemsConnected:
        if item[0] == conn[0] and item[1] == conn[1]:
            PeerSystemsConnected.remove(item)
            print('Removed Server for connection:'+str(PeerSystemsConnected))
            break

#list files on the server, manage rename incase delete
def ListServerContents(path):                                   
    directoryList = [file for file in os.listdir(path)]
    sendList = ''
    for item in directoryList:
        #[Debug]handle for delete file rename Debug
        if not item.endswith('*'):                    
            sendList = sendList + item + ', '
    sendList = sendList[:-2]
    return sendList

#list files tested
def ServerContentList(path):                         
    directoryList = [file for file in os.listdir(path)]
    sendList = ''
    for item in directoryList:
        sendList = sendList + item + ', '
    sendList = sendList[:-2]
    return sendList

#Map the file on global directory as [FileName, version, filedirectory, ip]
def AppendGlobalDirectory(string, fd, sharedSpaceMemory):                        
    if len(string) > 0:
        retList = (string.split(', '))
        for item in retList:
            file = item.rsplit(' ')
            if fd == 'self':
                add = [file[0], file[1], fd, fd]                    
            else:
                ip, port = fd.getpeername()
                add = [file[0], file[1], fd, ip]
            sharedSpaceMemory.append(add)

#return file with the latest version from the system
def GetLatestFileVersion(fileName, sharedSpaceMemory):     
    if len(sharedSpaceMemory) > 0:
        maximum = 0
        file = object
        for item in sharedSpaceMemory:
            if item[0] == fileName and int(item[1]) > maximum:
                maximum = int(item[1])
                file = item
            elif item[0] == fileName and int(item[1]) == maximum and item[2] == 'self':
                maximum = int(item[1])
                file = item
        if maximum == 0:
            return 'FILE NOT AVAILABLE'
        else:
            print('return file : ', file)
            return file
    else:
        print('File not available in shared system')

#searches for file in the shared space and gets details
def SearhFileInGlobalDirectory(fileName, sharedSpaceMemory):      
    returnList = []
    if len(sharedSpaceMemory) > 0:
        for item in sharedSpaceMemory:
            if item[0] == fileName:
                returnList.append(item)
        if len(returnList) == 0:
            return 'FILE NOT AVAILABLE'
        else:
            return returnList
    else:
        print('File not available in shared system')

#true if file is in shared memory
def IsAvailable(fileName, sharedSpaceMemory):                 
    for item in sharedSpaceMemory:
        if item[0] == fileName:
            return True
    return False

#list items available globally
def SendGlobalFilesName(sharedSpaceMemory):                           
    sendList = ''
    if len(sharedSpaceMemory) > 0:
        output = []
        for item in sharedSpaceMemory:
            #print('item------------>'+str(item)) 
            if item[0] not in output:
                #('item0------------>'+str(item[0]))
                output.append(item[0])
                #print("output--------->"+str(output))  
                sendList = sendList + item[0]+' ' + ', ' 
        sendList = sendList[:-2]
    return sendList

#[Debug]developer access, get file names and versions from file available globally. Helps in the version control 
def SendGlobalFilesName2(sharedSpaceMemory):                           
    sendList = ''
    if len(sharedSpaceMemory) > 0:
        output = []
        for item in sharedSpaceMemory:
            #print('item------------>'+str(item)) 
            if item[0] not in output:
                #('item0------------>'+str(item[0]))
                output.append(item)
                #print("output--------->"+str(output))  
                sendList = sendList + item[0]+' '+ item[1] + ' , ' 
        sendList = sendList[:-2]
    return sendList

#[Debug] For Version Control, Not used since SendGlobalFilesName2 handled well 
def SendGlobalFilesNameUnused(sharedSpaceMemory):                           
    sendList = ''
    if len(sharedSpaceMemory) > 0:
        for item in sharedSpaceMemory:
            sendList = sendList + item[0] + ' ' + item[1] + ', '
            # sendList = sendList + item[0] + ', '                   #orignal version
        sendList = sendList[:-2]
    return sendList

#inform servers to update shared file information, to handle modifications
def UpdateDirectory(connectedList, serverLock, globalList,
                    globalLock):                                    
    directory = ListServerContents(SingleMemoryIllusion)
    print('directory updateDirectory ', directory)
    globalLock.acquire(True)
    globalList.clear()
    AppendGlobalDirectory(directory, 'self', globalList)
    globalLock.release()
    message = 'updateDirectory '
    directory2 = message + directory
    # send own Directory List to all other connected servers
    serverLock.acquire(True)
    if len(PeerSystemsConnected) == 0:
        serverLock.release()
        return
    else:
        for items in connectedList:
            items[2].sendall(directory2.encode())
    serverLock.release()

#[Debug]update shared file list for all connected servers
def UpdateSharedFilesNameList(directory, connectedList, serverLock):
    message = 'update '
    directory2 = message + directory
    # send own Directory List to all other connected servers
    serverLock.acquire(True)
    for items in connectedList:
        items[2].sendall(directory2.encode())
    serverLock.release()

#[Debug]maintain changes and handle failure
def UpdateSharedList(sharedSpaceMemory, globalLock, connectedList, serverLock):
    directory = ListServerContents(SingleMemoryIllusion)
    globalLock.acquire(True)
    sharedSpaceMemory.clear()
    AppendGlobalDirectory(directory, 'self', sharedSpaceMemory)
    globalLock.release()

    message = 'update2 ' + directory
    serverLock.acquire(True)
    if len(connectedList) == 0:
        serverLock.release()
        return
    else:
        for conn in connectedList:
            conn[2].sendall(message.encode())
    serverLock.release()

#return array of [file,version] structure
def returnListofFiles(string):                                              
    returnList = []
    if len(string) > 0:
        retList = (string.split(', '))
        for item in retList:
            file = item.rsplit(' ')
            add = [file[0], file[1]]
            returnList.append(add)
    return returnList

#Handle sending most recent file to servers to keep them updated on boot
def SendMostRecent(oldFileName, newFileName, socketfd, PeerSystemsConnected, serverLock, sharedSpaceMemory, globalLock):
    message = 'download ' + newFileName
    socketfd.sendall(message.encode())
    receive = socketfd.recv(1024)
    os.rename(oldFileName, newFileName)
    with open(newFileName, 'wb') as fd:
        while True:
            if receive.decode().endswith('aosppdfs'):
                receive = receive[:-8]
                fd.write(receive)
                break
            fd.write(receive)
            receive = socketfd.recv(1024)
        fd.close()
    #UpdateDirectory(PeerSystemsConnected, serverLock, sharedSpaceMemory, globalLock)


#[Debug] for version control issues
def DeleteFiles():
    for file in os.listdir(SingleMemoryIllusion):
        if file.endswith("*"):
            os.remove(file)

# -------------------------------------->Threads Classes<----------------------------------------------------------

class ServerConnectionsThread(threading.Thread):
    def __init__(self, server, serverLock, globalLock, sharedSpaceMemory, PeerSystemsConnected, que):
        threading.Thread.__init__(self)
        self.server = server
        self.serverLock = serverLock
        self.globalLock = globalLock
        self.sharedSpaceMemory = sharedSpaceMemory
        self.PeerSystemsConnected = PeerSystemsConnected
        self.que = que

    def run(self):
        while True:
            acceptServer, address = self.server.accept()
            self.serverLock.acquire(True)
            bool = ConnectedIPs(address, self.PeerSystemsConnected)
            self.serverLock.release()
            if bool:
                acceptServer.close()
            else:
                print('Connected Successfully with Server: ', address)
                connectedSockets = [address[0], address[1], acceptServer]
                self.serverLock.acquire(True)
                self.PeerSystemsConnected.append(connectedSockets)
                print(self.PeerSystemsConnected)
                self.serverLock.release()
                currentPeerMemory = ServerContentList(SingleMemoryIllusion)
                localList = returnListofFiles(currentPeerMemory)
                acceptServer.sendall(currentPeerMemory.encode())
                received = acceptServer.recv(1024)
                remoteDirectory = received.decode()
                remoteList = returnListofFiles(remoteDirectory)
                for local in localList:
                    for remote in remoteList:
                        if local[1] == '*':
                            continue
                        elif local[0] == remote[0] and remote[1] == '*':
                            oldFileName = local[0] + ' ' + local[1]
                            newFileName = local[0] + ' *'
                            os.rename(oldFileName, newFileName)
                        elif local[0] == remote[0] and int(local[1]) < int(remote[1]):
                            print(local, remote)
                            oldFileName = local[0] + ' ' + local[1]
                            newFileName = remote[0] + ' ' + remote[1]
                            SendMostRecent(oldFileName, newFileName, acceptServer, self.PeerSystemsConnected, self.serverLock, self.sharedSpaceMemory, self.globalLock)
                try:
                    serverConnThread = ServerOperationsThread(connectedSockets, self.globalLock, self.sharedSpaceMemory, acceptServer,
                                                              self.serverLock, self.PeerSystemsConnected, self.que)
                    serverConnThread.start()
                    serverLock.acquire(True)
                    length = len(PeerSystemsConnected)

                    if length == 2:
                        DeleteFiles()
                    serverLock.release()
                except:
                    print("Error in starting the system and updating the shared memory. Consider restarting the system")


class ServerOperationsThread(threading.Thread):
    def __init__(self, address, globalLock, sharedSpaceMemory, filehandler, serverLock, PeerSystemsConnected, que):
        threading.Thread.__init__(self)
        self.address = address
        self.globalLock = globalLock
        self.sharedSpaceMemory = sharedSpaceMemory
        self.filehandler = filehandler
        self.serverLock = serverLock
        self.PeerSystemsConnected = PeerSystemsConnected
        self.que = que

    def run(self):
        while True:
            try:
                data = self.filehandler.recv(1024)
                #print('data:----------------> ', data)
                receivedData = data.decode()
                print('receivedData ----------------->', receivedData)
                if receivedData == '':
                    print('Server Disconnected!')
                    self.serverLock.acquire(True)
                    ServerDisconnection(self.address, self.PeerSystemsConnected)
                    self.serverLock.release()
                    UpdateSharedList(self.sharedSpaceMemory, self.globalLock, self.PeerSystemsConnected, self.serverLock)
                    break
                else:
                    tokens = receivedData.split(' ', 1)
                    if tokens[0] == 'updateDirectory' and len(tokens) == 2:
                        # create new Global List and append tokens[1]
                        directory = ListServerContents(SingleMemoryIllusion)
                        self.globalLock.acquire(True)
                        self.sharedSpaceMemory.clear()
                        AppendGlobalDirectory(directory, 'self', self.sharedSpaceMemory)
                        AppendGlobalDirectory(tokens[1], self.filehandler, self.sharedSpaceMemory)
                        self.globalLock.release()

                        # send own Directory List to all connected servers
                        UpdateSharedFilesNameList(directory, self.PeerSystemsConnected, self.serverLock)
                    elif tokens[0] == 'update2' and len(tokens) == 2:           #update sharedSpaceMemory on server shutdown
                        self.globalLock.acquire(True)
                        AppendGlobalDirectory(tokens[1], self.filehandler, self.sharedSpaceMemory)
                        self.globalLock.release()
                    elif tokens[0] == 'create' and len(tokens) == 2:
                        self.filehandler.sendall('ready aosppdfs'.encode())
                        response = self.filehandler.recv(1024)
                        fi = ''
                        while True:
                            response = response.decode()
                            if response.endswith('aosppdfs'):
                                response = response[:-8]
                                fi = fi + response
                                break
                            fi = fi + response
                            response = self.filehandler.recv(1024)
                        #--#print('fi : ', fi)
                        fd = open(tokens[1], 'w')
                        fd.write(fi)
                        fd.close()
                        print('file %s created' % tokens[1])
                        time.sleep(0.5) #test
                        UpdateDirectory(self.PeerSystemsConnected, self.serverLock, self.sharedSpaceMemory,
                                        self.globalLock)
                    elif tokens[0] == 'delete' and len(tokens) == 2:
                        fileName = tokens[1].rsplit(' ')
                        newFileName = fileName[0] + ' *'
                        os.rename(tokens[1], newFileName)
                        UpdateDirectory(self.PeerSystemsConnected, self.serverLock, self.sharedSpaceMemory,
                                        self.globalLock)
                    elif tokens[0] == 'update' and len(tokens) == 2:
                        self.globalLock.acquire(True)
                        AppendGlobalDirectory(tokens[1], self.filehandler, self.sharedSpaceMemory)
                        self.globalLock.release()
                    elif tokens[0] == 'download' and len(tokens) == 2:
                        # check if it has the file
                        print('tokens[0] ServerThread: ', tokens[0])
                        with open(tokens[1], 'rb') as fd:
                            load = fd.read(1024)
                            while load:
                                #--#print(load)
                                self.filehandler.sendall(load)
                                load = fd.read(1024)
                            fd.close()
                            self.filehandler.sendall('aosppdfs'.encode())
                    elif tokens[0] == 'upload' and len(tokens) == 2:
                        print('tokens[0] ServerThread: ', tokens[0])
                        oldFileName = tokens[1]
                        file = oldFileName.rsplit(' ')
                        version = int(file[1])
                        version = version + 1
                        newFileName = file[0] + ' ' + str(version)
                        os.rename(oldFileName, newFileName)
                        self.filehandler.sendall('ready aosppdfs'.encode())
                        response = self.filehandler.recv(1024)
                        fi = ''
                        while True:
                            response = response.decode()
                            if response.endswith('aosppdfs'):
                                response = response[:-8]
                                fi = fi + response
                                break
                            fi = fi + response
                            response = self.filehandler.recv(1024)
                        fd = open(newFileName, 'w')
                        fd.write(fi)
                        fd.close()
                        time.sleep(0.5)  # test
                        UpdateDirectory(self.PeerSystemsConnected, self.serverLock, self.sharedSpaceMemory,
                                        self.globalLock)
                    else:
                        fi = ''
                        while True:
                            if data.decode().endswith('aosppdfs'):
                                fi = fi + data.decode()
                                break
                            else:
                                fi = fi + data.decode()
                                data = self.filehandler.recv(1024)
                        self.que.put(fi)
            except:
                print('Server Disconnected!')
                self.filehandler.close()
                break


class ClientConnectionsThread(threading.Thread):
    def __init__(self, client, clientLock, PeerClientsConnected, PeerSystemsConnected, serverLock, globalLock, sharedSpaceMemory,
                 que):
        threading.Thread.__init__(self)
        self.client = client
        self.clientLock = clientLock
        self.PeerClientsConnected = PeerClientsConnected
        self.PeerSystemsConnected = PeerSystemsConnected
        self.serverLock = serverLock
        self.globalLock = globalLock
        self.sharedSpaceMemory = sharedSpaceMemory
        self.que = que

    def run(self):
        while True:
            acceptClient, address = self.client.accept()
            print('Server successfully connected with Client at ', address)
            connectedSockets = [address[0], address[1], acceptClient]
            
            self.clientLock.acquire(True)
            self.PeerClientsConnected.append(connectedSockets)
           
            self.clientLock.release()
            try:
                clientConnectionThread = ClientOperationThread(self.PeerSystemsConnected, self.serverLock, self.globalLock,
                                                                self.sharedSpaceMemory, acceptClient, que)
                clientConnectionThread.start()
            except:
                print("Client connections are not properly established! Please restart client!")


class ClientOperationThread(threading.Thread):
    def __init__(self, PeerSystemsConnected, serverLock, globalLock, sharedSpaceMemory, filehandler, que):
        threading.Thread.__init__(self)
        self.PeerSystemsConnected = PeerSystemsConnected
        self.serverLock = serverLock
        self.globalLock = globalLock
        self.sharedSpaceMemory = sharedSpaceMemory
        self.filehandler = filehandler
        self.que = que

    def run(self):
        while True:
            try:
                data = self.filehandler.recv(1024)
                command = data.decode()
                if command == '':
                    print('Client Disconnected!')
                    break
                else:
                    tokens = command.split(' ', 1)

                    if tokens[0] == 'ls' and len(tokens) == 1:
                        print('tokens[0] ClientThread: ', tokens[0])
                        self.globalLock.acquire(True)
                        sendList = SendGlobalFilesName(self.sharedSpaceMemory)
                        print('sharedSpaceMemory------->'+ str(self.sharedSpaceMemory))
                        self.globalLock.release()
                        if sendList == '':
                            msg = 'THERE ARE NO FILES AVAILABLE!'
                            self.filehandler.sendall(msg.encode())
                        else:
                            self.filehandler.sendall(sendList.encode())

                    elif tokens[0] == 'ls2' and len(tokens) == 1:
                        print('tokens[0] ClientThread: ', tokens[0])
                        self.globalLock.acquire(True)
                        sendList = SendGlobalFilesName2(self.sharedSpaceMemory)
                        print(self.sharedSpaceMemory)
                        self.globalLock.release()
                        if sendList == '':
                            msg = 'THERE ARE NO FILES AVAILABLE!'
                            self.filehandler.sendall(msg.encode())


                        else:
                            self.filehandler.sendall(sendList.encode())
                        
     
                    #elif tokens[0] == 'delete' and len(tokens) == 2:
                        #self.globalLock.acquire(True)
                        #fileList = SearhFileInGlobalDirectory(tokens[1], self.sharedSpaceMemory)
                        #print('fileDelete : ', fileList)
                        #self.globalLock.release()
                        #if fileList == 'FILE NOT AVAILABLE':
                    #        message = 'FILE %s CANNOT BE DELETED AS IT DOES NOT EXISTS!' % tokens[1]
                    #        self.filehandler.sendall(message.encode())
                    #    else:
                    #        for file in fileList:
                    #            if file[2] == 'self':
                    #                oldFileName = file[0] + ' ' + file[1]
                    #                newFileName = file[0] + ' *'
                    #                os.rename(oldFileName, newFileName)
                    #                if len(fileList) == 1:
                    #                    UpdateDirectory(self.PeerSystemsConnected, self.serverLock, self.sharedSpaceMemory,
                    #                                self.globalLock)
                    #            else:
                    #                command = command + ' ' + file[1]
                    #                file[2].sendall(command.encode())
                    #        self.filehandler.sendall('deleted'.encode())

                    elif tokens[0] == 'download' and len(tokens) == 2:
                        print('tokens[0] ClientThread: ', tokens[0])
                        self.globalLock.acquire(True)
                        file = GetLatestFileVersion(tokens[1], self.sharedSpaceMemory)
                        self.globalLock.release()
                        if file == 'FILE NOT AVAILABLE':
                            # send message - file not available
                            msg = ('FILE %s IS NOT AVAILABLE!' % tokens[1])
                            self.filehandler.sendall(msg.encode())
                        elif file[2] == 'self':
                            # send file from server
                            fileName = file[0] + ' ' + file[1]
                            with open(fileName, 'rb') as fd:
                                load = fd.read(1024)
                                while load:
                                    self.filehandler.sendall(load)
                                    load = fd.read(1024)
                                fd.close()
                                self.filehandler.sendall('aosppdfs'.encode())
                        else:
                            command = 'reconnect ' + file[3]
                            self.filehandler.sendall(command.encode())
                            print('Client redirected to another server')

                    elif tokens[0] == 'upload' and len(tokens) == 2:
                        self.filehandler.sendall('ready'.encode())
                        print('File yet to be recieved from client')
                        response = self.filehandler.recv(1024)
                        fi = ''
                        while True:
                            response = response.decode()
                            if response.endswith('aosppdfs'):
                                response = response[:-8]
                                fi = fi + response
                                break
                            else:
                                fi = fi + response
                                response = self.filehandler.recv(1024)
                        #--#print('response from client ', fi)
                        self.globalLock.acquire(True)
                        fileList = SearhFileInGlobalDirectory(tokens[1], self.sharedSpaceMemory)
                        print('file', fileList)
                        self.globalLock.release()
                        if fileList == 'FILE NOT AVAILABLE' or fileList is None:    # FILE CREATION
                            fileName = tokens[1] + ' 1'         # create file on 'self' server
                            fd = open(fileName, 'w')
                            fd.write(fi)
                            fd.close()
                            print('file created')

                            message = 'create ' + fileName      # create file on other server
                            fi = fi + 'aosppdfs'
                            #--#print('fi imp: ', fi)

                            isFound = False
                            conn = []
                            serverLock.acquire(True)
                            length = len(PeerSystemsConnected)
                            if length > 0:
                                index = randint(0, length - 1)
                                conn = PeerSystemsConnected[index]
                                isFound = True
                            serverLock.release()

                            if isFound:
                                print('Sending file %s to Server %s' % (tokens[1], conn[0]))
                                conn[2].sendall(message.encode())
                                data = self.que.get()
                                data = data[:-9]
                                print('recveived from server : ', data)
                                if data == 'ready':
                                    conn[2].sendall(fi.encode())
                                    print('File %s sent to Server %s' % (tokens[1], conn[0]))
                            else:
                                UpdateDirectory(self.PeerSystemsConnected, self.serverLock, self.sharedSpaceMemory, self.globalLock)
                        else:
                            for file in fileList:
                                if file[2] == 'self':
                                    oldFileName = file[0] + ' ' + file[1]
                                    version = int(file[1])
                                    version = version + 1
                                    newFileName = file[0] + ' ' + str(version)
                                    os.rename(oldFileName, newFileName)
                                    fd = open(newFileName, 'w')
                                    fd.write(fi)
                                    fd.close()
                                    print('file uploaded on server')
                                    if len(fileList) == 1:
                                        UpdateDirectory(self.PeerSystemsConnected, self.serverLock, self.sharedSpaceMemory,
                                                        self.globalLock)
                                else:
                                    fi = fi + 'aosppdfs'
                                    print('file upload command sent to another server')
                                    command = command + ' ' + file[1]
                                    file[2].sendall(command.encode())
                                    data = self.que.get()
                                    data = data[:-9]
                                    print('queue read: ', data)
                                    print('Confirmed: File uploading!')
                                    if data == 'ready':
                                        file[2].sendall(fi.encode())
                                        print('file uploaded on another server')

                    elif tokens[0] == 'create' and len(tokens) == 2:
                        self.globalLock.acquire(True)
                        isFound = IsAvailable(tokens[1], self.sharedSpaceMemory)
                        self.globalLock.release()
                        if isFound == True:
                            self.filehandler.sendall('found'.encode())
                        else:
                            self.filehandler.sendall('notfound'.encode())

                    elif tokens[0] == 'refresh' and len(tokens) == 1:
                        UpdateDirectory(self.PeerSystemsConnected, self.serverLock, self.sharedSpaceMemory, self.globalLock)

                    else:
                        msg = ('INVALID COMMAND!')
                        self.filehandler.sendall(msg.encode())
            except:
                print('Client Disconnected!')
                self.filehandler.close()
                break

# Main Method START
serverLock = threading.Lock()
clientLock = threading.Lock()
globalLock = threading.Lock()

SingleMemoryIllusion = os.getcwd()+ '/ServerMemory'
os.chdir(SingleMemoryIllusion)

que = queue.Queue()
sharedSpaceMemory = []
#server ip's, to connect to
Peers = [['192.168.0.111', 9999], ['192.168.0.113', 9999],['192.168.0.137', 9999], ['192.168.0.102', 9999]]      
PeerSystemsConnected = []
PeerClientsConnected = []


# Listening to Server Connection Requests
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

port = 9999
server.bind(('', port))
print("Server Listening socket bound to port %s" % (port))
server.listen(5)
try:
    serverThreadListen = ServerConnectionsThread(server, serverLock, globalLock, sharedSpaceMemory, PeerSystemsConnected, que)
    serverThreadListen.start()
except:
    print("Error: UNABLE TO START SERVER LISTENING THREAD!")

# Listening to Client Connection Requests
client = socket.socket()
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

port = 9998
client.bind(('', port))
print("Client Listening socket bound to port %s" % (port))
client.listen(5)
try:
    clientThreadListen = ClientConnectionsThread(client, clientLock, PeerClientsConnected, PeerSystemsConnected, serverLock,
                                               globalLock, sharedSpaceMemory, que)
    clientThreadListen.start()
except:
    print("Client socket cant be connected! Please try again after checking the ip provided")

# Global Directory Appending
globalLock.acquire(True)
currentPeerMemory = ListServerContents(SingleMemoryIllusion)
AppendGlobalDirectory(currentPeerMemory, 'self', sharedSpaceMemory)
globalLock.release()

# Connection Requests
for conn in Peers:
    serverLock.acquire(True)
    bool = ConnectedIPs(conn, PeerSystemsConnected)
    serverLock.release()
    if bool:
        continue
    else:
        print('Trying connection with Server at : ', conn)
        #print("debug=============>"+ conn[0], conn[1])
        serverEnd = socket.socket()
        serverEnd.settimeout(3)
        try:
            temp = serverEnd.connect_ex((conn[0], conn[1]))
            serverEnd.settimeout(None)
            if temp == 0:
                connectedSockets = [conn[0], conn[1], serverEnd]
                serverLock.acquire(True)
                PeerSystemsConnected.append(connectedSockets)
                print('Servers were connected Successfully')
                print(PeerSystemsConnected)
                serverLock.release()
                currentPeerMemory = ServerContentList(SingleMemoryIllusion)
                localList = returnListofFiles(currentPeerMemory)
                serverEnd.sendall(currentPeerMemory.encode())
                received = serverEnd.recv(1024)
                remoteDirectory = received.decode()
                remoteList = returnListofFiles(remoteDirectory)
                for local in localList:
                    for remote in remoteList:
                        if local[1] == '*':
                            continue
                        elif local[0] == remote[0] and remote[1] == '*':
                            oldFileName = local[0] + ' ' + local[1]
                            newFileName = local[0] + ' *'
                            os.rename(oldFileName, newFileName)
                        elif local[0] == remote[0] and int(local[1]) < int(remote[1]):
                            print(local, remote)
                            oldFileName = local[0] + ' ' + local[1]
                            newFileName = remote[0] + ' ' + remote[1]
                            SendMostRecent(oldFileName, newFileName, serverEnd, PeerSystemsConnected, serverLock, sharedSpaceMemory, globalLock)
                try:
                    serverConnThread = ServerOperationsThread(connectedSockets, globalLock, sharedSpaceMemory, serverEnd, serverLock,
                                                              PeerSystemsConnected, que)
                    serverConnThread.start()
                    time.sleep(0.5)
                    UpdateDirectory(PeerSystemsConnected, serverLock, sharedSpaceMemory, globalLock)
                    serverLock.acquire(True)
                    length = len(PeerSystemsConnected)
                    if length == 2:
                        DeleteFiles()
                    serverLock.release()
                except:
                    print("Shared Memory can't be updated, please restart again")
        except socket.error:
            print("Cannot connect to server at this time " + conn[0], conn[1])


