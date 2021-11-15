# Logan Carlile
# HLPC-Server
# 11/14/2021

import argparse
import socket
import threading
import sys
import logging
import time
import os
import platform

def getArgs():
    """This function will retrive arguments from the user via terminal arguments"""

    # get necesary arguments from the command line

    parser = argparse.ArgumentParser(description="This is the HLPC-server")

    # create a mutually exclusive argument group to determine the mode that the server will operate

    serverModeSelect = parser.add_mutually_exclusive_group(required=True)

    # option to start the server

    serverModeSelect.add_argument('--start',
                                  action='store_true',
                                  help='Use this argument, combined with an arguments in Start Server, to control server')

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

    serverControlGroup.add_argument('--power-outtage',
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

            # exit cleanly

            sys.exit()

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

# if this program is being run directly

if __name__ == "__main__":

    # initialize logging

    loggingInit()

    # determine host os

    getOsPlatform()

    # retrive arguments from user

    argsObj = getArgs()

    # determine what mode the server should run in

    # if the start argument was specified

    if argsObj.start:

        # initialize the server and set to the server object

        serverObj = serverInit(argsObj.host, argsObj.port)

        # start the serverDaemon

        serverDaemon()

    # if the control argument was specified

    elif argsObj.control:
        print('Control')
        pass