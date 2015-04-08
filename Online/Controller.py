#!/usr/bin/env python

"""
This Module runs the main loop for sample collection. It can communicate with a unix socket to interface with remote computers
and also creates a control object to pass settings about sensors and other aspects of the sample collection process.

Authored by Simon Kitchen 15/03/2015

"""

import Sensors
import Pumps
import RTPlotting as RTP
import sys
import time
import socket
import os
import TriggerSetting


class control:
    #code
    def __init__(self):
        
        if sys.platform == "linux2":
            setFile = open(r"SamplerSettings-RPi Copy.txt", 'r')
        else:
            setFile = open(r"SamplerSettings-Windows.txt", 'r')
        
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
        
        #print "CO2 address is: %s" % setList[0]
        #print "PressureAddress: %s" % setList[1]
        #print "PumpAddress: %s" % setList[2]
        #print "testLength: %d" % int(setList[3])
        #print "secDivision: %d" % int(setList[4])
        #print "controlSelection: %s" % setList[5]
        
        self.CO2Address = setList[0]
        self.PressureAddress = setList[1]
        self.PumpAddress = setList[2]
        self.testLength = int(setList[3])
        self.secDivision = int(setList[4])
        self.controlSelection = setList[5]
        #print self.CO2Address
        #print "trying to make sensor List"
        self.sensors = Sensors.sensorList(self.CO2Address, self.PressureAddress)
        self.sensors.CO2.triggerValue = float(setList[6])
        self.sensors.Pressure.triggerValue = int(setList[7])
        self.pumpVoltage = int(setList[8])
        
        self.myPump = Pumps.output_controller(self.PumpAddress, self.pumpVoltage) #, voltage = self.pumpVoltage)
        self.logging = True            #save CO2, Pressure and other data to txt file?
        self.collectionRun = True      #Run the sample collection pump when the gating algorithm returns True?
        self.CO2DrawThrough = False      #Run the pump constantly to draw air through the CO2 sensor?
        self.displayGraphLocal = False  #Plots the graph in a matplotlib animation locally
        self.displayGraphRemote = True  #Writes CO2, Pressure and other data to a socket that can be picked up by
                                            # Richard's web interface
        self.MFC = True     # Flag if whether MFC is attached or not
        self.volumeCollectionLimit = 50
        
        if self.controlSelection == 'ui':
            self.controlSelection = raw_input("type c, p or f depending on which sensor you want to control with: ")
        
        if self.testLength == 'ui':
            self.testLength = int(raw_input("enter number of seconds to collect data: "))
    
    def close(self):
        self.sensors.CO2.commLink.close()
        self.sensors.Pressure.commLink.close()
        self.myPump.commLink.close()
    
    def Runner(self, remoteComms):
        
        self.sock = remoteComms.sock
        
        self.timeStart = time.time()
        FileTime = self.timeStart
        timeS = [self.timeStart]
        self.collecting = 0
        #print "time start is: %s" % self.timeStart
        
        if sys.platform == "linux2":
            dataStore = r"/home/pi/datafiles/"
        else:
            dataStore = r"C:\Users\simon.kitchen\Documents\Software\Sandbox\Python\Test_rig\Sampling\datafiles\\"
            # Look for datafiles directory one level above this file's location
            #dataStore = os.path.join(os.path.dirname(__file__), "..", "datafiles")
        
        #Set up sampler settings and get breathing pattern:
        print "Now collecting for trigger calculation"
        setupFileName = dataStore+str(int(FileTime))+" SetupConfig.txt"
        self.dataFile = open(setupFileName, 'w')
        statusHolder = self.collectionRun       # ensure the pump doesn't run during this phase and collect the wrong sample
        self.collectionRun = False
        self.localLoop(10, remoteComms)    #callibration time, 30sec should allow 5 breaths, a good average
        self.dataFile.close()
        self.collectionRun = statusHolder       #turn pump back on to previous settings
        
        triggerCal = TriggerSetting.TriggerCalcs()
        TriggerVals = triggerCal.calculate(setupFileName)
        self.sensors.CO2.triggerValue = TriggerVals[0]
        self.sensors.Pressure.triggerValue = TriggerVals[1]
        
        print "CO2 Trigger Val is: %f" % TriggerVals[0]
        print "Pressure Trigger Val is: %f" % TriggerVals[1]
        #print "*******************************************"
        #raw_input()
        
        self.dataFile = open(dataStore+str(int(FileTime))+".txt", 'w')
        #self.dataFile = open(str(int(self.timeStart))+".txt", 'w')
        
        if self.CO2DrawThrough == True:
            #print "turning pump on"
            self.myPump.turnOnOff(1)
            time.sleep(1)
        
        print "measurement loop"
        
        if self.displayGraphLocal == True:
            self.Grapher = RTP.graphing()
            self.Grapher.runGraphingLoop(self)
        elif self.displayGraphLocal == False:
            self.localLoop(self.testLength, remoteComms)
            
        print "finished collecting"
        self.myPump.turnOnOff(0)
        self.dataFile.close()
        print "done!!!"
        
    def localLoop(self, testLength, remoteComms):
        self.timeStart = time.time()
        counter = 0
        self.collectionLimitReached = False
        if MFC:
            self.sensors.Flow.reset(self.timeStart)
        
        #while time.time()-self.timeStart <= testLength and not self.collectionLimitReached:
        if MFC:
            while time.time()-self.timeStart <= testLength and self.sensors.Flow.collectedVolume() < self.volumeCollectionLimit:
                CO2, Pressure, Flow, timeStamp = self.sensors.getReadings(self)
                counter = counter + 1
                commands = remoteComms.receive()
                if commands.find("stopsampling") >= 0:
                    break
                TS = float(counter)/self.secDivision - (time.time()-self.timeStart)
                if TS < 0:
                    TS = 0
                time.sleep(TS)
            
            tt = (time.time()-self.timeStart)
            print "Total test time was: %f" % tt
            vv = self.sensors.Flow.collectedVolume()
            print "Total test collection volume was: %f" % vv
            print "so which one stopped it: %f, %f" %(testLength, self.volumeCollectionLimit)
        else:
            while time.time()-self.timeStart <= testLength:
                CO2, Pressure, timeStamp = self.sensors.getReadings(self)
                counter = counter + 1
                commands = remoteComms.receive()
                if commands.find("stopsampling") >= 0:
                    break
                TS = float(counter)/self.secDivision - (time.time()-self.timeStart)
                if TS < 0:
                    TS = 0
                time.sleep(TS)

class Communications:
    def __init__(self):
        print "connecting to socket"
        server_address = '/tmp/lucidity.socket'

        # Make sure the socket exists
        if not os.path.exists(server_address):
            raise Exception("No socket at %s" % server_address)
        
        # Create a UDS socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setblocking(0)   # important - don't block on reads
        
        # Try and connect to socket.  Output any error and fall over.
        try:
            self.sock.connect(server_address)
        except socket.error, msg:
            print >>sys.stderr, msg
            sys.exit(1)
    def receive(self):
        # Return either an empty string (if nothing received)
        # or the contents of any incoming message
        try:
            return self.sock.recv(1024)
        except socket.error:
            return ""
    
    



def mainProgram(remoteControl = True):
    myControl = control()
    myComms = Communications()
    
    while True:
        
        try:
            print "waiting for response from web interface"
            while remoteControl == True:
                
                #myComms loop until got a start command
                commString = myComms.receive()
                if commString.find("startsampling") >= 0:
                    print "found something"
                    break
                
                time.sleep(1)
        except KeyboardInterrupt:
            myControl.close()
            myComms.sock.close()
            sys.exit()
            
    
        myControl.Runner(myComms)
        noInput = True
        while noInput == True:
            userInput = raw_input("Collection cycle complete, type r to repeat, or q to quit: ")
            if userInput == 'r':
                noInput = False
            elif userInput == 'q':
                myControl.close()
                myComms.sock.close()
                sys.exit()
            else:
                print "invalid arguement, please enter r or q"
    

if __name__ == '__main__':
    
    remoteControl = True
    mainProgram(remoteControl)
    
    