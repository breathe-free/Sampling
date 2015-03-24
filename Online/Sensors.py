#!/usr/bin/env python

from serial import Serial
import time

class sensorList:
    def __init__(self, CO2Ad, PressureAd):
        self.CO2 = CO2_sensor(CO2Ad)
        self.Pressure = Pressure_sensor(PressureAd)
        
    def getReadings(self, controls):
        PVal = self.Pressure.getReading()
        #print "got pressure"
        CVal = self.CO2.getReading()
        #print "got CO2"
        timeStamp = time.time()
        
        if isinstance(controls.sensors.CO2.triggerValues, list):
            if controls.controlSelection == "c" and CVal >= controls.sensors.CO2.triggerValues[0] and controls.collecting==0:
                print "collecting"
                controls.collecting = controls.sensors.CO2.triggerValues[0]
            
            elif controls.controlSelection == "c" and CVal <= controls.sensors.CO2.triggerValues[1] and controls.collecting>=1:
                print "stopped collecting"
                controls.collecting = 0
            
            elif controls.controlSelection == "p" and PVal >= controls.sensors.Pressure.triggerValues[0] and controls.collecting==0:
                print "collecting"
                controls.collecting = controls.sensors.Pressure.triggerValues[0]
            
            elif controls.controlSelection == "p" and PVal <= controls.sensors.Pressure.triggerValues[1] and controls.collecting>=1:
                print "stopped collecting"
                controls.collecting = 0
            else:
                print "continue as is"
                pass
            
        
        else:
            if controls.controlSelection == "c" and CVal >= controls.sensors.CO2.triggerValues:
                print "collecting"
                controls.collecting = controls.sensors.CO2.triggerValues
        
            elif controls.controlSelection == "p" and PVal >= controls.sensors.Pressure.triggerValues:
                print "collecting"
                controls.collecting = controls.sensors.Pressure.triggerValues
        
            else:
                controls.collecting = 0
        
        if controls.collectionRun == True:
            #print "now at pump"
            if controls.collecting >= 1:
                
                controls.myPump.turnOnOff(1)
            else:
                controls.myPump.turnOnOff(0)
        
        dataString = "%s, %s, %s, %s\n" % (str(timeStamp), str(PVal), str(CVal), str(controls.collecting))
        
        if controls.logging == True:
            #print "writing file"
            #print dataString
            controls.dataFile.write(dataString)
        if controls.displayGraphRemote == True:
            
            controls.sock.sendall(dataString)
           
        
        return CVal, PVal, timeStamp
    
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