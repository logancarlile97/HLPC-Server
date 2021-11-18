# Logan Carlile
# HLPC-Server
# 11/14/2021

import argparse
from genericpath import exists
import socket
import threading
import sys
import logging
import time
import os
import platform

# set environment variables

# get path where the script is located

scriptPath = os.path.dirname(os.path.abspath(__file__))

# set the data folder

dataPath = os.path.join(scriptPath, "data")

# set the name and path of the force outage file. if this file exists
#  then the HLPC Server will force agents to shutdown clients

outageFilePath = os.path.join(dataPath, "outageNow")

# server running file, this file is created when the server starts 
# and is deleted when the server stops, it prevents the server from 
# being started more than once

serverRunningPath = os.path.join(dataPath, "serverIsRunning")

# server shutdown file, this file is created to safely shutdown the server

serverShutdownFilePath = os.path.join(dataPath, "shutdownServerNow")

def getArgs():
    """This function will retrive arguments from the user via terminal arguments"""

    # get necesary arguments from the command line

    parser = argparse.ArgumentParser(description="This is the HLPC-server")

    # create a mutually exclusive argument group to determine the mode that the server will operate

    serverModeSelect = parser.add_mutually_exclusive_group(required=True)

    # option to start the server

    serverModeSelect.add_argument('--start',
                                  action='store_true',
                                  help='Use this argument, combined with an arguments in Start Server, to start server')

    # option to stop a running server

    serverModeSelect.add_argument('--stop',
                                  action='store_true',
                                  help='Use this argument to stop a running server')

    # option to send commands to a running server

    serverModeSelect.add_argument('--control',
                                  action='store_true',
                                  help='Use this argument, combined with an argument in Control Server, to control server')

    # Create an argument group for starting the server

    serverStartGroup = parser.add_argument_group(
        'Start Server', 'Commands to use with the --start argument')

    # get the ip address to bind to

    serverStartGroup.add_argument('-ip',
                                  '--host',
                                  metavar='host',
                                  type=str,
                                  nargs='?',
                                  default='127.0.0.1',
                                  help='IP Address for the server to listen on (default: 127.0.0.1)')

    # get the port to bind to

    serverStartGroup.add_argument('-p',
                                  '--port',
                                  metavar='port',
                                  type=int,
                                  nargs='?',
                                  default=5540,
                                  help='Port for the server to listen on (default: 5540)')

    # create an argument group for controling a server after it has started

    serverControlGroup = parser.add_argument_group(
        'Control Server', 'Commands to use with the --control argument')

    # argument that, if used, will simulate a power outtage, triggering a shutdown event

    serverControlGroup.add_argument('--force-outage',
                                    dest='pwrOutSim',
                                    action='store_true',
                                    help='Use this option to simulate a power outage on a running HLPC server')

    # parse the arguments into the args object

    argsObj = parser.parse_args()

    # return the argsObj

    return argsObj


def loggingInit():
    """This function will initialize logging"""

    # create a global variable log

    global log

    # assign logging to the log object

    log = logging

    # setup a config for logging

    log.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] - %(message)s')


def preServerInitChecks():

    """This function will ensure all needed directories exist 
    before attempting to start the server"""

    # log that pre server start checks are being run

    log.info(f"Running Pre Server Start Checks")

    # log check for data folder

    log.info(f"Ensuring data folder exists at path {dataPath}")

    # if the data directory does not exist

    if not(os.path.exists(dataPath)):
        # tell the user

        log.warning(f"Data folder not found attempting to create it")
        
        # try to create the folder

        try:
            os.makedirs(dataPath)

        # if it fails tell the user

        except Exception as e:
            log.critical(f"Could not create the data folder due to error:")
            log.critical(f"{e}")

            # and exit the program 

            sys.exit()

    # otherwise tell the user it was found

    else:
        log.info(f"Data folder found... proceeding")
    
    # check if the server is already running

    log.info(f"Checking if the server is already running")

    # if the server is already running

    if os.path.exists(serverRunningPath):

        # tell the user

        log.error(f"The server seems to already be running")
        log.error(f"If this is not correct please delete the following file:")
        log.error(f"{serverRunningPath}")

        # exit cleanly

        sys.exit()

    # tell user that pre server start checks are complete

    log.info(f"Pre Server Start Checks finished proceeding")


def serverInit(ip, port):
    """This function will attempt to initialize a socket server bound to ip and port.
    If it fails it will print an error and exit to program.
    If sucessful it will return the socket object"""

    # tell the user that the server is being initialized

    log.info(f"HLPC Server is starting...")

    # create an ipv4 socket object

    serverObj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # attempt to bind the serverObj to the specified ip and port

    try:

        # tell user that attempt to bind is being made

        log.info(f"Attempting to bind to {ip} on port {port}")

        serverObj.bind((ip, port))

    # if the bind fails

    except Exception as e:

        # tell the user the server could not be started

        log.error(f"HLPC server could not be started!")

        # report an error to the user

        log.error(f"Attempt to bind to {ip}:{port} failed with error: {e}")

        # exit the program

        sys.exit()

    # if the bind does not fail

    else:

        # begin to listen on the bound interface

        serverObj.listen()

        # tell user what the server has been bound to

        log.info(f"HLPC server is listening on {ip}:{port}")

    # tell the user that the server has been started

    log.info(f"HLPC server has been started")

    # create the server running file 

    open(serverRunningPath, 'w').close()

    # return the server object

    return serverObj


def handleClient(conn, client_addr):
    """This function will handle comms to a connected client
    It will take conn a socket object for the client and addr which 
    contains the ip address of the client."""

    # set needed variables

    disconnect = '!DISCONNECT'  # set the disconnect message
    headerLength = 64           # length of the header message
    format = 'utf-8'            # set the encodeing format

    # report new clients address info

    log.info(f"New connection from {client_addr[0]}:{client_addr[1]}")

    # set connected to true

    connected = True

    # loop until client disconnects

    while connected:

        # get the header from client

        header = conn.recv(headerLength).decode(format)

        # if the recieved header is not blank

        if header:

            # get message length from the header text

            msgLength = int(header)

            # retrive the client message

            msg = conn.recv(msgLength).decode(format)

            # close the connection if client sends disconnect message

            if msg == disconnect:
                connected = False

            # print the clients message

            log.info(f"{client_addr[0]}:{client_addr[1]} sent {msg}")

            # tell the client the message was recieved

            conn.send("Msg received".encode(format))

    log.info(f"Closing connection to {client_addr[0]}:{client_addr[1]}")

    # close the connection

    conn.close()


def serverListen():
    """This function will listen for new connections. 
    When a new connection is detected a thread will be 
    created to handle the client"""

    # loop indefinetly

    while True:

        # look for new connections and assign them to
        #   conn and client_addr

        conn, client_addr = serverObj.accept()

        # create a new thread to handle the newly connected client and assign it the the client object

        clientObj = threading.Thread(
            target=handleClient, args=(conn, client_addr), daemon=True)

        # start the new thread

        clientObj.start()

        # print the number of active connections

        log.info(f"Active Client Connections = {threading.active_count()-2}")


def getOsPlatform():

    """This function will return the os platform if the program can run on it. 
    Otherwise it will exit the program."""

    osPlatform = platform.system()

    # if detected os is windows

    if osPlatform == 'Windows':
        log.info(f"{osPlatform} operating system detected")
        return osPlatform

    # if detected os is Linux

    if osPlatform == 'Linux':
        log.info(f"{osPlatform} operating system detected")
        return osPlatform
    
    # otherwise 

    else:
        log.error(f'Unsupported operating system detected: {osPlatform}')
        sys.exit()


def forceOutage():

    """This function will perform the neccessary action to tell the 
    server to force the agents to shutdown"""

    # if the shutdownNow file already exists

    if os.path.exists(outageFilePath):

        # tell the user that a force shutdown is already being processed

        log.error(f"A force outtage command is already being processed")

    # if the file does not exist

    elif not(os.path.exists(outageFilePath)):

        # try to create it

        try:
            open(outageFilePath, 'a').close()

        # if it fails notify the user

        except Exception as e:
            log.error(f"Could not force an outtage due to the following error:")
            log.error(f"{e}")


def cleanup():

    """This function will handle cleanup of files when the server is stopped"""

    # log that the server is currently attempting cleanup

    log.info(f"Attempting server cleanup")

    # delete the outageNow file if it exists

    if os.path.exists(outageFilePath):
        log.info(f"Attempting to cleanup {outageFilePath}")
        os.unlink(outageFilePath)

    # delete the server running file if it exists

    if os.path.exists(serverRunningPath):
        log.info(f"Attempting to cleanup {serverRunningPath}")
        os.unlink(serverRunningPath)

    # delete the shutdownServerNow file if it exists

    if os.path.exists(serverShutdownFilePath):
        log.info(f"Attempting to cleanup {serverShutdownFilePath}")
        os.unlink(serverShutdownFilePath)

    # tell the user that the cleanup is complete

    log.info(f"Cleanup complete")
    

def serverStop():

    """This function will handle stopping the server"""

    # try to run the server cleanup

    try:
        cleanup()

    # if it fails tell the user

    except Exception as e:
        log.warning(f"The server was not able to perform a cleanup operation because of the following error:")
        log.warning(f"{e}")
        log.warning(f"This may cause future problems")

    # if cleanup ran succesfully tell the user

    else: 
        log.info(f"Server cleanup finished successfully")

    # exit cleanly

    sys.exit()


def serverDaemon():

    """This function will start serverListen in a thread and 
    wait for the user to shutdown the server"""

    # create a thread object for serverListen

    serverListenThreadObj = threading.Thread(target=serverListen, daemon=True)

    # start the thread

    serverListenThreadObj.start()

    # loop indefinetly

    while True:

        # if the user hits the keyboard interupt

        try:

            # wait for 5 seconds to prevent overutilization of resources

            time.sleep(5)

        except KeyboardInterrupt:

            # log the keypress

            log.critical(
                f"KeyboardInterupt detected, shutting down the server")

            # stop the server

            serverStop()

        # if the shutdown file exists then

        if os.path.exists(serverShutdownFilePath):
            
            # tell the user

            log.warning(f"shutdownServerNow file detected shuting down server now")

            # stop the server

            serverStop()

# if this program is being run directly

if __name__ == "__main__":

    # initialize logging

    loggingInit()

    # retrive arguments from user

    argsObj = getArgs()

    # determine what mode the server should run in

    # if the start argument was specified

    if argsObj.start:

        # do the prechecks before starting the server

        preServerInitChecks()

        # initialize the server and set to the server object

        serverObj = serverInit(argsObj.host, argsObj.port)

        # start the serverDaemon

        serverDaemon()

    # if the control argument was specified

    elif argsObj.control:
        
        # if user specified to force a power outage

        if argsObj.pwrOutSim:
            
            # run the force outage function

            forceOutage()

        # if user does not specify a control command

        else:

            log.error(f'Could not detect valid control command')

    # if the stop argument was specified

    elif argsObj.stop:

        # if the data folder does not exist exit the program as there 
        # is no way the server would start without it

        if not(os.path.exists(dataPath)):
            log.info("No server is currently running")
            sys.exit()


        # if a server is not running

        if not(os.path.exists(serverRunningPath)):

            # tell the user

            log.info(f"No server is currently running")

            # perform a cleanup

            cleanup()

            # exit the program 

            sys.exit()

        # otherwise attempt to stop the server

        else:
            
            # tell the user that the server if being stopped

            log.info(f"Attempting to stop HLPC Server...")

            # create the server shutdown file

            open(serverShutdownFilePath, 'w').close()

            # tell the user that the program will wait to see if the server stops

            log.info(f"Waiting for server to stop...")

            # wait 20 seconds for the server to stop

            time.sleep(20)

            # if the server did not shutdown

            if os.path.exists(serverRunningPath):

                # report an error to the user

                log.error(f"Could not shutdown the server, please manually check to see if it is running!")

                # exit cleanly

                sys.exit()

            # otherwise 

            else: 

                # tell the user the server was shutdown

                log.info(f"Server successfully shutdown")

                # exit the program 

                sys.exit()