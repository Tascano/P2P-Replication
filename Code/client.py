"""----------------------------------------------------------------------------------------------------------
A Simple Peer to Peer File System
-Ambrose Tuscano, Jayalakshmi

Client1: 
IP: 192.168.0.123

next Server to connect in case of failure are given in serverips.txt which acts as a config file


Changes: 1. Choosing a server for connecting is at random, if you want to join a particular server we would
            suggest hardcoding it in ServerIPs list. Random server is choosen to act as a load balancer. 
----------------------------------------------------------------------------------------------------------"""



#------------------> Imports <------------------------------
import socket
import os
import subprocess
import filecmp
import difflib
import datetime
import random
import time 

#------------------> Ip Imports <------------------------------

with open("serverips.txt") as f:              
#functions like config file
    content = f.readlines()
f.close()
serverIps = [x.strip() for x in content]     
#client will try among the following list incase of failure.

#------------------> Functions <------------------------------

def ClientServerConnection(port):   
    for i in range(2*len(serverIps)): 
    #to ensure that client connects with random probablity.
        
        ip = random.choice(serverIps) 
        print(ip)
        server = socket.socket()
        server.settimeout(1)
        temp = server.connect_ex((ip, port))
        server.settimeout(None)
        if temp == 0:
            print('Connected With : ', ip)
            return server
    return 'Please try again, all servers seem to be down'

#this ensures that if file is on other server the client is connected to that server. Also helps in resilient structure
def CSNewConnection(server, port):
    server.close()
    server = ClientServerConnection(port)
    if server == 'NO SERVERS AVAILABLE!':
        print('NO SERVERS AVAILABLE!')
        exit(0)
    return server

# Main ------------------------------------------------------------------------------------------------------------------

baseDirectory = os.getcwd()
clientDirectory = os.getcwd()+ '/ClientMemory'
os.chdir(clientDirectory)
port = 9998

server = ClientServerConnection(port)

versionList = []
toadd = ''

if server == 'NO SERVERS AVAILABLE!':
    print('NO SERVERS AVAILABLE!')
else:
        
    while True:
        try:
            MenuCard ="list ----> List files on shared Memory(Server) \n create <file> ----> Create a file named <file> \n read <file> ----> Read the file on current Client \n  download <file> ----> Download the file from server(can searve both like read from server and also write on server)\n appendf <file> text ----> Appends text to file on Client space \n  upload <file> ----> Uploads file to Server \n quit ----> quit gracefully. \n"
            commands = input('Enter Command:\n ---------Type commandcard for command list------- \n')
            inputs = commands.split(' ', 2)
            print('commands: ', commands)

            # ------------------break free gracefully-----------------  
            if inputs[0] == 'quit' and len(inputs) == 1:
                break
            
            # ------------------See list of commands for my system-----------------  
            elif inputs[0] == 'commandcard' and len(inputs) == 1:
                print(MenuCard)

            # ------------------Print list of files present on shared memory-----------------  
            elif inputs[0] == 'list' and len(inputs) == 1:
                server.sendall(('ls').encode())
                data = server.recv(1024)
                
                if data.decode() == '':
                    server = CSNewConnection(server, port)
                    continue

                files = data.decode()
                print(files)


            # ------------------See files present with their versions, this is for debugging and version control-----------------  
            elif inputs[0] == 'developerslist' and len(inputs) == 1:
                server.sendall(('ls2').encode())
                data = server.recv(1024)
                
                if data.decode() == '':
                    server = CSNewConnection(server, port)
                    continue

                versionList = data.decode()
                print(versionList)

            # ------------------Create new file and distribute it over servers-----------------                       
            elif inputs[0] == 'create' and len(inputs) == 2:
                server.sendall(commands.encode())
                data = server.recv(1024)
                if data.decode() == '':
                    server = CSNewConnection(server, port)
                    continue
                if data.decode() == 'found':
                    print('A file with the name %s exists, please download the file if needed!' % inputs[1])
                else:
                    fi = open(inputs[1], 'w+')
                    message = 'upload ' + inputs[1]
                    server.sendall(message.encode())
                    response = (server.recv(1024)).decode()
                    if response == 'ready':
                        fi = open(inputs[1], 'rb')
                        load = fi.read(1024)
                        while load:
                            server.sendall(load)
                            load = fi.read(1024)
                        fi.close()
                        server.sendall('aosppdfs'.encode())
                        print('File %s Uploaded on Server and sent for replication!' % inputs[1])

            #-------------------- Physically upload file into the servers incase of inconsistency---------            
            elif inputs[0] == 'upload' and len(inputs) == 2:
                print('wait for 10 seconds time, this will ensure that no other version has been changed due to possible simulteneous access!')
                #to ensure that other clients had access too and have file versioning check in meantime as our system takes 
                #max 4 seconds for transfer of file ~1mb.

                time.sleep(10)  
                server.sendall(('ls2').encode())
                data = server.recv(1024)
                
                if data.decode() == '':
                    server = CSNewConnection(server, port)
                    continue

                versionList2 = data.decode()
                print('versionList=======>'+str(versionList))
                print('versionList2=======>'+str(versionList2))

                if versionList==versionList2: 
                    if os.path.isfile(inputs[1]):
                        server.sendall(commands.encode())
                        response = (server.recv(1024)).decode()
                        if response == '':
                            server = CSNewConnection(server, port)
                            continue
                        print('response ', response)
                        if response == 'ready':
                            fi = open(inputs[1], 'rb')
                            load = fi.read(1024)
                            while load:
                                server.sendall(load)
                                load = fi.read(1024)
                            fi.close()
                            server.sendall('aosppdfs'.encode())
                            print('File %s Uploaded on Server!' % inputs[1])
                    else:
                        print('FILE %s DOES NOT EXISTS!' % inputs[1])
                else:
                    print("File has been modified please download first and then append: " + toadd )

                    print("Please make it a point to append again before uploading")
                    toadd = ''
    

        
            # ------------------Read Local File-----------------    
            elif inputs[0] == 'read' and len(inputs) == 2:
                print("File exists:"+str(os.path.exists(clientDirectory+'/'+inputs[1])))
                if(os.path.exists(clientDirectory+'/'+inputs[1]) == True):
                    print("---------------------------------")
                        # Open file for reading
                    fileObject = open(clientDirectory+'/'+inputs[1], "r")
                        # Read a file line by line and print in the terminal
                    for line in fileObject:
                        print(line)
                    print("---------------------------------")
                else:       
                    print("Download file if doesnt exists \n Command: download <filename>")
            
            # ------------------Append to Local File and Upload it later-----------------
            
            elif inputs[0] == 'appendf' and len(inputs) == 3:
                print("File exists:"+str(os.path.exists(clientDirectory+'/'+inputs[1])))
                toadd = ''+ inputs[2]
                server.sendall(('ls2').encode())
                data = server.recv(1024)
                if data.decode() == '':
                    server = CSNewConnection(server, port)
                    continue
                versionList = data.decode()
                print('versionList=======>'+versionList)
                if(os.path.exists(clientDirectory+'/'+inputs[1]) == True):
                    fileObject = open(clientDirectory+'/'+inputs[1], "a")
                    fileObject.write("\n"+inputs[2]) 
                    fileObject.close()


                    
                else:       
                    print("Create file if doesnt exists \n Command: create <filename>")

            # ------------------Delete Global File, can't work out due to the vesioning-----------------    
            #elif inputs[0] == 'delete' and len(inputs) == 2:
            #    server.sendall(commands.encode())
            #    receive = server.recv(1024)
            #    if receive.decode() == '':
            #       server = CSNewConnection(server, port)
            #        continue
            #    error = 'FILE %s CANNOT BE DELETED AS IT DOES NOT EXISTS!' % inputs[1]
            #    success = 'FILE %s DELETED!' % inputs[1]
            #    if receive.decode() == error:
            #        print(error)
            #    elif receive.decode() == 'deleted':
            #        print(success)
            #
            #Had bugs with the renaming, plan was to delete file from client, and change the version to absolute 
            #character in server. But there were bugs while trying to rename and delete the file

            # ------------------Download updated file and open it for reading-----------------    
            elif inputs[0] == 'download' and len(inputs) == 2:
                server.sendall(commands.encode())
                recvd_data = server.recv(1024)
                if recvd_data.decode() == '':
                    server = CSNewConnection(server, port)
                    continue
                error = 'FILE %s IS NOT AVAILABLE!' % inputs[1]
                remoteData = recvd_data.decode()
                tokens = remoteData.split(' ', 1)
                #print('token =====> '+str(tokens))
                if tokens[0] == 'reconnect':
                    server.close()
                    server = socket.socket()
                    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    temp = server.connect((tokens[1], port))
                    print('Connected With : ', tokens[1])
                    server.sendall(commands.encode())
                    recvd_data = server.recv(1024)
                    error = 'FILE %s IS NOT AVAILABLE!' % inputs[1]
                    decoded = recvd_data.decode()
                    if decoded == error:
                        print(error)
                    else:
                        with open(inputs[1], 'wb') as fi:
                            while True:
                                if recvd_data.decode().endswith('aosppdfs'):
                                    recvd_data = recvd_data[:-8]
                                    fi.write(recvd_data)
                                    break
                                fi.write(recvd_data)
                                recvd_data = server.recv(1024)
                            fi.close()
                        print('File %s Downloaded!' % inputs[1])
                        before = os.stat(inputs[1])[8]
                        subprocess.call(['Notepad.exe', inputs[1]])  #change notepad with append(overwrite will be a waste)
                        after = os.stat(inputs[1])[8]
                        if before == after:
                            print('File %s was not changed, so it current copy is updated ' % inputs[1])
                            continue
                        else:
                            message = 'upload ' + inputs[1]
                            server.sendall(message.encode())
                            response = (server.recv(1024)).decode()
                            if response == 'ready':
                                fi = open(inputs[1], 'rb')
                                load = fi.read(1024)
                                while load:
                                    server.sendall(load)
                                    load = fi.read(1024)
                                fi.close()
                                server.sendall('aosppdfs'.encode())
                                print('File %s Uploaded on Server!' % inputs[1])
                elif remoteData == error:
                    print(error)
                else:
                    with open(inputs[1], 'wb') as fi:
                        while True:
                            if recvd_data.decode().endswith('aosppdfs'):
                                recvd_data = recvd_data[:-8]
                                fi.write(recvd_data)
                                break
                            fi.write(recvd_data)
                            recvd_data = server.recv(1024)
                        fi.close()
                    print('File %s Downloaded!' % inputs[1])
                    before = os.stat(inputs[1])[8]
                    subprocess.call(['Notepad.exe', inputs[1]])
                    after = os.stat(inputs[1])[8]
                    if before == after:
                        print('File %s was not changed, so it current copy is updated' % inputs[1])
                        continue
                    else:
                        message = 'upload ' + inputs[1]
                        server.sendall(message.encode())
                        response = (server.recv(1024)).decode()
                        if response == 'ready':
                            fi = open(inputs[1], 'rb')
                            load = fi.read(1024)
                            while load:
                                server.sendall(load)
                                load = fi.read(1024)
                            fi.close()
                            server.sendall('aosppdfs'.encode())
                            print('File %s Uploaded on Server!' % inputs[1])


            


            #------------- try to update the lists -----------        
            elif inputs[0] == 'refresh' and len(inputs) == 1:
                server.sendall(commands.encode())
            else:
                print('INVALID COMMAND!')

        except socket.error as e:
            try:
                print('Restarting Connection')
                #connection fails so restart connection to new server
                server = CSNewConnection(server, port) 
            except:
                print("Start client again!")

            
            
            
