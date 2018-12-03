# Curtis Naples
# C0457101
# Network Programming - Lab 2
import socket, math, sys, os

import threading
import time
from collections import deque

#-------------------------------------------------------------------------Client Handler--------------------------------------------------------------------------------------------

class ClientHandler(threading.Thread):
    def __init__(self, connection, address):
        threading.Thread.__init__(self)
        self.connection = connection
        self.address = address
    #------------------------------------RUN------------------------------------
    def run(self):
        #function used to iteravely top-down search directory for file in drive location
        def search_files(givenFN):
            if '/' in givenFN:
                sDirectory = givenFN.rsplit('/',1)[0] + '/'
                givenFN = givenFN.rsplit('/',1)[1]
            else:
                sDirectory = './'
            #searches through this and all subdirectories
            for dirpath, dirnames, files in os.walk(sDirectory):
                #print(files)
                for name in files:
                    #filename matches passed in name
                    if name == givenFN:
                        #trys to open the file to check for permission. More secure than R_OK and F_OK
                        try:
                            f = open(os.path.join(dirpath, name), "rb")
                            f.close()
                            return (os.path.join(dirpath, name))
                        except PermissionError:
                            return ("READ")
            #File not Found
            return("NF")



        try:
            if sys.argv[3] == '-v':
                errChkFlag = True
        except:
            errChkFlag = False

        s = self.connection
        addr = self.address
        s.sendto(('READY').encode("utf-8"), addr)
        request = s.recv(1024)
        lock = threading.Lock()
        #print(request.decode())
        print()
        print()
        

        #--------------------------------------------------------Client wants to get a file from server---------------------------------------
        if (request.decode()[:3] == 'GET' ):
            fileName = request.decode()[4:]
            if errChkFlag == True:
                print("\t     Command: GET " + fileName)

            #search function to find the file in this or any subdirectories checks if file exists and is readable
            search = search_files(fileName)
            #File not Found
            if search == "NF":
                s.sendto(("ERROR: "+ fileName +" not found on server").encode("utf-8"), addr)
                if errChkFlag == True:
                    print("\tSERVER ERROR: " + fileName + " not found on server")
                    print()
            
            #File not Readable    
            elif search == "READ":
                s.sendto(("\tERROR: " + fileName + " exists on server, unable to read ").encode("utf-8"), addr)
                if errChkFlag == True:
                    print("\tSERVER ERROR: " + fileName + " exists on server, unable to read ")
                    print()
            #File found and readable, start sending to client   
            else:
                #send OK to client
                s.sendto(("OK").encode("utf-8"), addr)
                
                #recieve READY from client
                ready = s.recv(1024).decode()
                if ready == "READY":
                    #send number of bytes to be sent
                    numBytes = os.path.getsize(search)
                    if errChkFlag == True:
                        print("\tSending number of bytes (" + str(numBytes) + " bytes) to client")
                    s.sendto(numBytes.to_bytes(8,"big"), addr)
                    
                    #recieve OK from Client
                    ok = s.recv(1024).decode()
                    if ok == "OK":
                        if errChkFlag == True:
                            print("\t Sending the file " + fileName + " to client")

                        
                        #---------------------------Loop that sends the file in 1024 byte packages to client-
                        
                        #opens file to be read in binary
                        filePack = open(search, "rb",3)
                        total = 0
                        while total < numBytes:
                            lock.acquire()
                            try:
                                peice = filePack.read(1024)
                            finally:
                                lock.release()
                            total += len(peice)
                            s.sendto(peice, addr)
                            #print(peice.decode(),"")
                        filePack.close()  
                        if errChkFlag == True:
                            print ("\t     " + fileName + " sent to client")#add timer here
                            print()
                        time.sleep(1)
                        #send DONE
                        s.sendto(("DONE").encode("utf-8"), addr)
                        

        #--------------------------------------------------Client wants to save a file on the server------------------------------------------
        elif (request.decode()[:3] == 'PUT' ):
            fileName = request.decode()[4:]
            if errChkFlag == True:
                print("\t     Command: PUT " + fileName)
            #send OK to client
            try:
                #s.settimeout(0.5)
                s.sendto(("OK").encode("utf-8"), addr)
                #recieve number of bytes to be sent from client
                numBytes = int.from_bytes(s.recv(1024),"big")
                #s.settimeout(None)
                if errChkFlag == True:
                    print("\tRecieving number of bytes (" + str(numBytes) + " bytes) from client")
                #send OK to client
                s.sendto(("OK").encode("utf-8"), addr)
            
                #-------------------------------------------loop to recieve file from client-

                if errChkFlag == True:
                    print("\tServer recieving file " + fileName + " ("+ str(numBytes)+" bytes)")
                #checks if a dirpath was given to search in and strips it off for new file
                if '/' in fileName:
                    newFile = fileName.rsplit('/',1)[1]
                else:
                    newFile = fileName
                lock.acquire()
                #opens new file if doesnt exist and/or appends to that file
                try:
                    f=open(newFile, "a+b",3)
                except:
                    s.sendto(("ERROR: " + newFile + " could not be saved to server, Permission Denied").encode("utf-8"), addr)
                    if errChkFlag == True:
                        print("\tSERVER ERROR - " + newFile + " could not be saved")
                        print()
                total = 0
                while total < numBytes:
                    data = s.recv(1024)
                    total += len(data)
                    #save the file in client dir
                    #print(data,end="")
                    f.write(data)
                f.close()
                lock.release()

                if errChkFlag == True:
                    print("\t Server saved "+ newFile +" in server directory")
                    print()
                #send DONE
                s.sendto(("DONE").encode("utf-8"), addr)
                
            except:
                #s.settimeout(None)
                s.sendto(("ERROR: " + fileName + " was not sent").encode("utf-8"), addr)
                if errChkFlag == True:
                    print("\tCLIENT ERROR - " + fileName + " was not sent")
                    print()
        #--------------------------------------------client wants to delete a file on the server--------------------------------------------
        elif (request.decode()[:3] == 'DEL' ):
            fileName = request.decode()[4:]
            if errChkFlag == True:
                print("\t     Command: DEL " + fileName)
            search = search_files(fileName)
            if search == "NF":
                s.sendto(("ERROR: " + fileName + " does not exist on server").encode("utf-8"), addr)
                if errChkFlag == True:
                    print("\tSERVER ERROR - " + fileName + " does not exist on server")
                    print()
            
            #File not Readable    
            elif search == "READ":
                s.sendto(("ERROR: " + fileName + " was found but couldn't be deleted on server").encode("utf-8"), addr)
                if errChkFlag == True:
                    print("\tSERVER ERROR - " + fileName + " was found but not deleted, Permission Denied")
                    print()
            #File found and readable, delete file   
            else:
                os.remove(search)
                #send DONE to client
                s.sendto(("DONE").encode("utf-8"), addr)
                if errChkFlag == True:
                    print("\tServer deleted "+ fileName +" in server directory")
                    print()
       



#-------------------------------------------------------------------------Manager Class----------------------------------------------------------------------------------

class Manager(threading.Thread):
        #change to init/self...
        def __init__(self):
            threading.Thread.__init__(self)
            self.runningSet = set()
            self.queue = deque()
            self.lock = threading.Lock()
            self.max = int(sys.argv[2])
        #add to the queue
        def addToQ(self, thread):
            self.lock.acquire()
            self.queue.append(thread)
            self.lock.release()
        def run(self):
            #Loops forever, must use task manager to kill
            while True:
                
                #1. check the running threads, if stopped, remove from RUNNING SET
                kick = []
                for thread in self.runningSet: 
                    if not thread.is_alive():
                        kick.append(thread)
                for thread in kick:
                        self.runningSet.remove(thread)
                #2 if QUEUE empty, sleep(1) return to top of loop
                if len(self.queue) == 0:
                    time.sleep(1)
                    continue
                #3 QUEUE has a thread
                else:  
                    #3.1 if RUNNING SET full, sleep(1) return to top of loop
                    if len(self.runningSet) >= self.max:
                        time.sleep(1)
                        continue
                    #3.2 if RUNNING SET has space
                    else:
                        #3.2.1 remove the next client thread from QUEUE
                        thread = self.queue.popleft()
                        #3.2.2 start/run the thread
                        thread.start()
                        #3.2.3 add thread to the RUNNING SET
                        self.runningSet.add(thread)
                        time.sleep(1)
               
        





#-------------------------------------------------------------------------Main--------------------------------------------------------------------------------------------



manager = Manager()
manager.start()

port = int(sys.argv[1])

#checks for error checking flag "-v"
try:
    if sys.argv[3] == '-v':
        errChkFlag = True
except:
    errChkFlag = False

#socket setup
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind( ("", port) )
s.listen(5)
while True:
    #waiting for connection
    conn, addr = s.accept()
    if errChkFlag == True:
        print("\tQueued client from " + str(addr[0]) + ":" +str(addr[1]))
    #connection success
    #starts a thread
    theThread = ClientHandler(conn, addr)
    #print(theThread)
    #adds to the client queue
    manager.addToQ(theThread)