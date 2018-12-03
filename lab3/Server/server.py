# Curtis Naples
# C0457101
# Network Programming - Lab 2
import socket, math, sys, os


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


#gets the port from arguement
port = int(sys.argv[1])
#checks for error checking flag "-v"
try:
    if sys.argv[2] == '-v':
        errChkFlag = True
except:
    errChkFlag = False

# Create the socket object using DGRAM
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Bind to the port. Using "" for the interface so it binds to all known interfaces, including "localhost".
socket.bind( ("", port) )
socket.listen(0)
#Servers stay open -- they handle a client, then loop back to wait for another client.
while True:
    if errChkFlag == True:
        print()
        print("\t     Waiting for Client Connection on Port " + str(port))
    # wait for a client to send a packet
    s, addr = socket.accept()

    s.sendto(('READY').encode("utf-8"), addr)
    #getting first request
    request = s.recv(1024)
    if errChkFlag == True:
        print("\tServer connected to client at " + str(addr[0]) + ":" +str(port))
    


    #--------------------------------------------------------Client wants to get a file from server------------------------------------------------
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
                    filePack = open(search, "rb")
                    total = 0
                    while total < numBytes:
                        peice = filePack.read(1024)
                        total += len(peice)
                        #print(peice.decode(),"")
                        s.sendto(peice, addr)              
                    filePack.close()  
                    if errChkFlag == True:
                        print ("\t     " + fileName + " sent to client")#add timer here
                        print()
                    #send DONE
                    s.sendto(("DONE").encode("utf-8"), addr)
                    

    #--------------------------------------------------Client wants to save a file on the server------------------------------------------
    elif (request.decode()[:3] == 'PUT' ):
        fileName = request.decode()[4:]
        if errChkFlag == True:
            print("\t     Command: PUT " + fileName)
        #send OK to client
        try:
            s.sendto(("OK").encode("utf-8"), addr)
            #recieve number of bytes to be sent from client
            numBytes = int.from_bytes(s.recv(1024),"big")
            
            if errChkFlag == True:
                print("\tRecieving number of bytes (" + str(numBytes) + " bytes) from client")
            #send OK to client
            s.sendto(("OK").encode("utf-8"), addr)
        
            #-------------------------------------------loop to recieve file from client-
            x=0
            #number of times to loop
            y =  int(numBytes / 1024)+1
            #print(y)
            if errChkFlag == True:
                print("\tServer recieving file " + fileName + " ("+ str(numBytes)+" bytes)")
            #checks if a dirpath was given to search in and strips it off for new file
            if '/' in fileName:
                newFile = fileName.rsplit('/',1)[1]
            else:
                newFile = fileName
            #opens new file if doesnt exist and/or appends to that file
            try:
                f=open(newFile, "a+b")
            except:
                s.sendto(("ERROR: " + fileName + " could not be saved to server, Permission Denied").encode("utf-8"), addr)
                if errChkFlag == True:
                    print("\tSERVER ERROR - " + fileName + " could not be saved")
                    print()
            total = 0
            while total < numBytes:
                data = s.recv(1024)
                total += len(data)
                #save the file in client dir
                #print(data,end="")
                f.write(data)
            f.close()
            if errChkFlag == True:
                print("\t Server saved "+ fileName +" in server directory")
                print()
            #send DONE
            s.sendto(("DONE").encode("utf-8"), addr)
            
        except:
            s.sendto(("ERROR: " + fileName + " was not sent").encode("utf-8"), addr)
            if errChkFlag == True:
                print("\tCLIENT ERROR - " + fileName + " was not sent")
                print()
    #--------------------------------------------client wants to delete a file on the server-------------------------------------------------
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
            
            
        
    

    
    
    

    