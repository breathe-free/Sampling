#!/usr/bin/env python

import Sensors
import Pumps
import RTPlotting as RTP
import sys
import time
import socket
import os


class control:
    #code
    def __init__(self):
        
        setFile = open("SamplerSettings.txt", 'r')
        allSettings = setFile.read()
        allSettings = allSettings.strip()
        allSettings = allSettings.split("\n")
        setFile.close()
        setList = []
        for i, setting in enumerate(allSettings):
            setting = setting.strip()
            #setting.strip("\r")
            #setting.strip("\n")
            #setting.strip("\r")
            #setting.strip("")
            setting = setting.split(" = ")
            
            for s in setting:
                s.strip()
                
            setList.append(setting[1])
        
        print "CO2 address is: %s" % setList[0]
        print "PressureAddress: %s" % setList[1]
        print "PumpAddress: %s" % setList[2]
        print "testLength: %d" % int(setList[3])
        print "secDivision: %d" % int(setList[4])
        print "controlSelection: %s" % setList[5]
        
        
        self.CO2Address = setList[0]
        self.PressureAddress = setList[1]
        self.PumpAddress = setList[2]
        self.testLength = int(setList[3])
        self.secDivision = int(setList[4])
        self.controlSelection = setList[5]
        print self.CO2Address
        print "trying to make sensor List"
        self.sensors = Sensors.sensorList(self.CO2Address, self.PressureAddress)
        self.sensors.CO2.triggerValue = float(setList[6])
        self.sensors.Pressure.triggerValue = int(setList[7])
        
        self.myPump = Pumps.output_controller(self.PumpAddress)
        self.logging = True            #save CO2, Pressure and other data to txt file?
        self.collectionRun = False      #Run the sample collection pump when the gating algorithm returns True?
        self.CO2DrawThrough = True      #Run the pump constantly to draw air through the CO2 sensor?
        self.displayGraphLocal = False  #Plots the graph in a matplotlib animation locally
        self.displayGraphRemote = True  #Writes CO2, Pressure and other data to a socket that can be picked up by
                                            # Richard's web interface
        
        
        
        if self.controlSelection == 'ui':
            self.controlSelection = raw_input("type c, p or f depending on which sensor you want to control with: ")
        
        if self.testLength == 'ui':
            self.testLength = int(raw_input("enter number of seconds to collect data: "))
        

    def Runner(self):
        
        if self.displayGraphRemote == True:
            server_address = '/tmp/lucidity.socket'

            # Make sure the socket exists
            if not os.path.exists(server_address):
                raise Exception("No socket at %s" % server_address)
            
            # Create a UDS socket
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            
            # Try and connect to socket.  Output any error and fall over.
            try:
                self.sock.connect(server_address)
            except socket.error, msg:
                print >>sys.stderr, msg
                sys.exit(1)
        
        
        
        self.timeStart = time.time()
        timeS = [self.timeStart]
        self.collecting = 0
        print "time start is: %s" % self.timeStart
        if sys.platform == "linux2":
            dataStore = r"/home/pi/datafiles/"
        else:
            dataStore = r"C:\Users\simon.kitchen\Documents\Software\Sandbox\Python\Test_rig\Sampling\datafiles\\"
        self.dataFile = open(dataStore+str(int(self.timeStart))+".txt", 'w')
        #self.dataFile = open(str(int(self.timeStart))+".txt", 'w')
        
        if self.CO2DrawThrough == True:
            print "turning pump on"
            self.myPump.turnOnOff(1)
            time.sleep(1)
        
        print "measurement loop"
        
        if self.displayGraphLocal == True:
            self.Grapher = RTP.graphing()
            self.Grapher.runGraphingLoop(self)
        elif self.displayGraphLocal == False:
            self.localLoop()
            
        print "finished collecting"
        self.myPump.turnOnOff(0)
        self.dataFile.close()
        if self.displayGraphRemote == True:
            self.sock.close()
        print "done!!!"
        
    def localLoop(self):
        self.timeStart = time.time()
        counter = 0
        while time.time()-self.timeStart < self.testLength:
            CO2, Pressure, timeStamp = self.sensors.getReadings(self)
            counter = counter + 1
            TS = float(counter)/self.secDivision - (time.time()-self.timeStart)
            if TS < 0:
                TS = 0
            time.sleep(TS)
        
        
    

if __name__ == '__main__':
    myControl = control()
    while True:
        myControl.Runner()
        noInput = True
        while noInput == True:
            userInput = raw_input("Collection cycle complete, type r to repeat, or q to quit: ")
            if userInput == 'r':
                noInput = False
            elif userInput == 'q':
                sys.exit()
            else:
                print "invalid arguement, please enter r or q"