#!/usr/bin/env python

from serial import Serial
import time

class sensorList:
    def __init__(self, CO2Ad, PressureAd):
        self.CO2 = CO2_sensor(CO2Ad)
        self.Pressure = Pressure_sensor(PressureAd)
        
    def getReadings(self, controls):          # this should be moved into Sensors as a function within sensorList
        PVal = self.Pressure.getReading()
        print "got pressure"
        CVal = self.CO2.getReading()
        print "got CO2"
        timeStamp = time.time()
        if controls.controlSelection == "c" and CVal >= self.CO2.triggerValue:
            print "collecting"
            controls.collecting = controls.sensors.CO2.triggerValue
    
        elif controls.controlSelection == "p" and PVal >= self.Pressure.triggerValue:
            print "collecting"
            controls.collecting = controls.sensors.Pressure.triggerValue
    
        else:
            controls.collecting = 0
        
        if controls.collectionRun == True:
            print "now at pump"
            controls.myPump.turnOnOff(controls.collecting)
        
        dataString = "%s, %s, %s, %s\n" % (str(timeStamp), str(PVal), str(CVal), str(controls.collecting))
        
        if controls.logging == True:
            print "writing file"
            print dataString
            controls.dataFile.write(dataString)
        if controls.displayGraphRemote == True:
            
            controls.sock.sendall(dataString)
           
        
        return CVal, PVal, timeStamp
    
    def setTriggerValues(self, controls):
        saveLoggingStatus = controls.logging
        controls.logging = False
        raw_input("put mask on, take 2 breaths then press any key")
        print "Starting respiration characterisation process\nBreathe normally for 15 seconds"
        
        
        
    
        timeStart = time.time()
        tempData = []
        CO2Data = []
        PressureData = []
        for i in range(15*controls.secDivision):
            print "looping for calibration: %d" % i
            CO2, Pressure, timeStamp = sensorPoll.getReadings(controls, logging = False)
            tempData.append([timeStamp - timeStart, CO2, Pressure])
            CO2Data.append(CO2)
            PressureData.append(Pressure)
            timeToWait = ((float(i+1)/float(controls.secDivision))-(time.time() - timeStart))
            if timeToWait < 0:
                timeToWait = 0
            time.sleep(timeToWait)
        
        CO2Min = (min(CO2Data))
        CO2Max = (max(CO2Data))
        PressureMin = (min(PressureData))
        PressureMax = (max(PressureData))
        
        print "CO2Min, CO2Max, PressureMin, PressureMax" 
        print CO2Min
        print CO2Max
        print PressureMin
        print PressureMax
        
        return CO2Min, CO2Max, PressureMin, PressureMax
        
        
        
    
    
    
    
    

class CO2_sensor: #designed for things like CO2, flow or pressure etc   HOW TO MERGE THE SENSOR TYPES?????
    def __init__(self, connection, samplePeriod = 0.2):
        self.connection = connection
        self.samplePeriod = samplePeriod
        self.triggerValue = 3.2

        self.commLink = self.initialiseConnection()
        

    def initialiseConnection(self):
        print r"%s" % self.connection
        conn = Serial(self.connection, writeTimeout = 3)    #9600 baud
        #conn = Serial("/dev/ttyUSB0", writeTimeout = 3)    #9600 baud
        print "starting connection"
        for i in range(0, 2):
            conn.write('K 2\r\n')
            time.sleep(0.1)
            conn.readline()
        conn.write(".\r\n")
        time.sleep(0.2)
        conn.readline()
        print "initialised CO2"
        return conn

    def getReading(self):
        self.commLink.write('z\r\n')
        readString = self.commLink.readline()
        readString = readString.strip()
        readString = readString.split()
        pp105 = float(readString[1]) # ppm/10! - not ppm
        CO2percent = pp105/1000
        return CO2percent


class Pressure_sensor: #Should be rolled into CO2_sensor and just called input sensor
    def __init__(self, connection, samplePeriod = 0.2):
        self.connection = connection
        self.samplePeriod = samplePeriod
        self.triggerValue = 350

        self.commLink = self.initialiseConnection()
        print "trying outside of IC:"
        self.commLink.write('r')
        print self.commLink.readline()

    def initialiseConnection(self):
        conn = Serial(self.connection, 9600, timeout = 3)
        time.sleep(1)
        conn.write('r')
        print conn.readline()
        print"initialised Pressure"
        return conn

    def getReading(self):
        self.commLink.write('r')
        #print "written r to Arduino"
        pressure = float(self.commLink.readline() )
        #print "got pressure"
        return pressure