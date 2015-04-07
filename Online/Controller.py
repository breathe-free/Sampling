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

import json
import csv


class Control:
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
        self.sensors.CO2.triggerValues = [float(setList[6]), float(setList[6])]
        self.sensors.Pressure.triggerValues = [int(setList[7]), int(setList[7])]
        self.pumpVoltage = int(setList[8])
        
        
        self.myPump = Pumps.output_controller(self.PumpAddress, self.pumpVoltage) #, voltage = self.pumpVoltage)
        self.logging = True            #save CO2, Pressure and other data to txt file?
        self.collectionRun = True      #Run the sample collection pump when the gating algorithm returns True?
        self.CO2DrawThrough = False      #Run the pump constantly to draw air through the CO2 sensor?
        self.displayGraphLocal = False  #Plots the graph in a matplotlib animation locally
        self.displayGraphRemote = True  #Writes CO2, Pressure and other data to a socket that can be picked up by
                                            # Richard's web interface
        
        
        
        
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
        self.sensors.CO2.triggerValues = TriggerVals[0]
        self.sensors.Pressure.triggerValues = TriggerVals[1]
        print type(TriggerVals)
        if isinstance(TriggerVals[0], list):
            print "*******************************************"
            for iii in range(2):
                print iii
                print "CO2 Trigger Val is: %f" % TriggerVals[iii][0]
                print "Pressure Trigger Val is: %f" % TriggerVals[iii][1]
        else:
            print"##############################################"
            print "CO2 Trigger Val is: %f" % TriggerVals[0]
            print "Pressure Trigger Val is: %f" % TriggerVals[1]
        
        
        
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
        while time.time()-self.timeStart <= testLength:
            CO2, Pressure, timeStamp = self.sensors.getReadings(self)
            counter = counter + 1
            commands = remoteComms.checkCommands()
            if commands is not None and commands.find("stopsampling") >= 0:
                break
            TS = float(counter)/self.secDivision - (time.time()-self.timeStart)
            if TS < 0:
                TS = 0
            time.sleep(TS)
    
class Communications:
    def __init__(self, controls):
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
        
        self.STATES = self.enum(
            INITIALISING = "initialising",
            WAITING      = "waiting",
            CALIBRATING  = "calibrating",
            ANALYSING    = "analysing",
            COLLECTING   = "collecting",
        )
        self.ACTIVE_STATES = [ self.STATES.CALIBRATING, self.STATES.ANALYSING, self.STATES.COLLECTING ]
        
        self.support = Support_Functions()
    
    def receive(self):
        
        rbuffer = ''
        while True:
            try:
                incoming = self.sock.recv(1024)
                rbuffer += incoming
            except socket.error:
                # nothing to read
                yield None
                continue
    
            while rbuffer.find("\n") != -1:
                line, rbuffer = rbuffer.split("\n", 1)
                try:
                    yield json.loads(line)
                except ValueError, e:
                    print >>sys.stderr, str(e)
                    print >>sys.stderr, line
    
    def change_state(self, new_state, message=None, severity=None):
        if self.state != new_state:
            message = "State changed to %s." % new_state
            severity = "info"
        self.state = new_state
        self.emit_state(message=message, severity="info")
    
    def emit_state(self, **kwargs):
        h = {"state": self.state}
        for key,val in kwargs.iteritems():
            h[key] = val
        self.send(json.dumps(h) + "\n") 
    
    def send(self, message):
        self.sock.sendall(message)
        
    def enum(self, **enums):
        return type('Enum', (), enums)
    
    def checkCommands(self):        #sort of equivalent to run in Richard's main function
        
        # read from sock
        received = receive().next()
        if received is not None and 'command' in received:
            # act on information received
            print "Received: %s" % received
            
            do_what = received['command']
            if do_what == "stop":
                self.change_state(self.STATES.WAITING)
                return "stopsampling"
            
            elif do_what == "start":
                self.emit_state(message="Using settings: " + json.dumps(received['settings']), severity="info")
                self.change_state(self.STATES.CALIBRATING)
                return "startsampling"

            elif do_what == "request_state":
                self.emit_state()
            
            elif do_what == "request_settings_current":
                self.emit_state(settings=self.settings)
            
            elif do_what == "apply_settings_default":
                self.settings = self.support.loadSettings("default")
                self.emit_state(settings=self.settings, message="Loaded default settings.", severity="info")
            
            elif do_what == "apply_settings_user":
                self.settings = self.support.loadSettings("user")
                self.emit_state(settings=self.settings, message="Loaded user settings.", severity="info")
            
            elif do_what == "save_settings":
                self.user_settings = received['settings']
                self.support.saveSettings(self.user_settings)
                self.emit_state(settings=self.settings, message="Saved user settings.", severity="info")

class Support_Functions:
    def __init__(self):
        pass
    def saveSettings(self, settings):
        with open("UserDefinedSettings.txt", "w") as outfile:
            json.dump(settings, outfile)            #save to user settings file (overwrite)
    
    def loadSettings(self, source):
        if source == "user":
            pass
        elif source == "default":
            pass
        else:
            pass
        return settings
    
    
    
    

def mainProgram(remoteControl = True):
    myControl = Control()
    myComms = Communications(myControl)
    
    while True:
        
        try:
            print "waiting for response from web interface"
            while remoteControl == True:
                
                #myComms loop until got a start command
                commString = myComms.checkCommands()
                if commString is not None and commString.find("startsampling") >= 0:
                    print "found something"
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print "Keyboard used to interrupt - do I need to close something here?"
            pass
            #myControl.close()
            #myComms.sock.close()
            
    
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
    
    