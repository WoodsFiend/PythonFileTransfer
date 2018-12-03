# Curtis Naples
# C0457101
# Network Programming - Lab 3

#---------------------ARGUEMENTS SYNTAX----------------------
#   
# host, port, command, file_name (DIR/file_name searchs DIR/SUBDIRS for the file)
import socket, sys, os, subprocess, re, math, time


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


#checks that the port number is valid
try:
    port = int(sys.argv[2])
except ValueError:
    print()
    print('\tInvalid Port Number')
    print('\t Please Try Again')
    sys.exit()

#Create the socket using DGRAM and try to connect
host = sys.argv[1]
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.settimeout(3.0)

#try to connect to server
try:
    s.connect((host, port))
except socket.gaierror as e:
    print()
    print('\tConnection To Host Failed')
    print('\t    Check  Host/Port')
    print()
    print()
    sys.exit()


#packs arguments command and file_name then sends to server
command = sys.argv[3]
fileName = sys.argv[4]



#checks that server is ready
try:
    ready = s.recv(1024).decode()
except Exception as e:
    print()
    print("\t  Connection Timeout")
    print("\t   Check Host/Port")
    print()
    print()
    sys.exit()
#checks if the server is ready
if ready == "READY":
    # Receive the first response OK, DONE, ERROR
    try:
        #send the packet with command and file_name. 
        s.send((command + ' ' + fileName).encode("utf-8"))
        data1 = s.recv(1024).decode()
    except Exception as e:
        print()
        print("\t  Connection Timeout")
        sys.exit()

    #------------------------------------------------------Recieve requested file FROM server------------COMMAND = GET-----------------------------------
    if(data1 == 'OK' and command == 'GET'):
        s.send(("READY").encode("utf-8"))
        #recieve the number of bytes that are going to be sent from server
        try:
            numBytes = int.from_bytes(s.recv(1024),"big")
        except Exception as e:
            print()
            print("\t  Connection Timeout NUMBYTES")
            print()
            print()
            sys.exit()
        print()
        print("\t      Client recieving bytes (" + str(numBytes)+ " bytes)")
        #print(numBytes)
        #send OK to server
        s.send(("OK").encode("utf-8"))

        print()
        print("\tClient recieving file " + fileName + " ("+ str(numBytes)+" bytes)")
        
        #checks if a dirpath was given to search in and strips it off for new file
        if '/' in fileName:
            newFile = fileName.rsplit('/',1)[1]
        else:
            newFile = fileName
        
        #opens new file if doesnt exist and appends to that file
        try:
            f=open(newFile, "a+b",3)
        except Exception as e:
            print()
            print("  CLIENT ERROR - " + newFile + " could not be saved on client, Permission Denied")
            print()
            print()
            sys.exit()

         #------------------------------------------------Loop to recieve file from server-
        total = 0
        while total < numBytes:
            data = s.recv(1024)
            total += len(data)
            #save the file in client dir
            #print(data,end="")
            f.write(data)
        f.close()
        #recieve DONE from server
        try:
            data = s.recv(1024).decode()
        except Exception as e:
            print(e)
            print("\t  Client Error - done was not recieved from server")
            print()
            print()
            sys.exit()
        
        if "DONE" in data:       
                print()
                print('\t  ' + newFile + " was saved to client directory")
                print()
                print()
        sys.exit()

    #-----------------------------------------------------------------------Send file to the server--------------COMMAND = PUT------------------------------------------
    elif(data1 == 'OK' and command == 'PUT'):
        search = search_files(fileName)
        #File not Found
        if search == "NF":
            print()
            print("\tCLIENT ERROR - " + fileName + " not found on client")
            print()
            print()
            sys.exit()
        #File not Readable    
        elif search == "READ":
            print()
            print("\tCLIENT ERROR - " + fileName + " found on client, Permission Denied")
            print()
            print()
            sys.exit()
        #send the number of bytes to be sent to server
        numBytes = os.path.getsize(fileName)
        print()
        print("\t      Client sending bytes (" + str(numBytes)+ " bytes)")
        s.send(numBytes.to_bytes(8,"big"))       
        
        #recieve OK from the server
        try:
            ok = s.recv(1024).decode()
            
        except Exception as e:
            print()
            print("\t  Connection Timeout")
            sys.exit()
            
        if ok == "OK":
            #---------------------------Loop that sends the file in 1024 byte packages to server-
            
            print()
            print('\tClient sending file ' + fileName + ' (' + str(numBytes) + ' bytes)')
            
            #opens file to be read in binary
            filePack = open(search, "rb",3)
            total = 0
            while total < numBytes:
                peice = filePack.read(1024)
                #print(peice.decode(),"")
                total += len(peice)
                s.send(peice)
            filePack.close()
            
            #recieve DONE from server
            done = s.recv(1024).decode()
            if done == "DONE":
                print()
                print('\t  ' + fileName + ' saved to server directory')
                print()
                print()
                sys.exit()    
            elif 'ERROR:' in done:
                #if the response contains ERROR cut ERROR out of message and print
                print()
                print("  Server Error - " + re.split("ERROR:",done, flags=re.IGNORECASE)[1])
                print()
                print()
            sys.exit()
    #-------------------------------------------------------------------Delete a file from the server---------------COMMAND = DEL------------------------------------------
    elif (data1 == 'DONE' and command == 'DEL'):
        print()
        print('\tClient deleted file ' + fileName + " on the server")
        print()
        print()
        sys.exit()

    elif 'ERROR:' in data1:
        #if the response contains ERROR cut ERROR out of message and print
        print()
        print("  Server Error - " + re.split("ERROR:",data1, flags=re.IGNORECASE)[1])
        print()
        print()

    
