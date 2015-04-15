#!/usr/bin/env python

from serial import Serial
import time

class sensorList:
    def __init__(self, CO2Ad, PressureAd, MFC):
        self.CO2 = CO2_sensor(CO2Ad)
        self.Pressure = Pressure_sensor(PressureAd)
        self.MFC = MFC
        if self.MFC:
            self.Flow = Flow_sensor(self.Pressure.commLink)
  
    def getReadings(self, controls):
        PVal = self.Pressure.getReading()
        #print "got pressure"
        CVal = self.CO2.getReading()
        #print "got CO2"
        if self.MFC:
            FVal = self.Flow.getReading()
        timeStamp = time.time()
        
        controls = self.selectionMatrix(controls,CVal, PVal)
        
        if controls.collectionRun == True:
            #print "now at pump"
            if controls.collecting != 0:
                
                controls.myPump.turnOnOff(1)
            else:
                controls.myPump.turnOnOff(0)
        
        if self.MFC:
            self.Flow.currentFlow = FVal
            self.Flow.currentTime = timeStamp
            dataString = "%s, %s, %s, %s, %s\n" % (str(timeStamp), str(PVal), str(CVal), str(FVal), str(controls.collecting))
        else:
            dataString = "%s, %s, %s, %s\n" % (str(timeStamp), str(PVal), str(CVal), str(controls.collecting))
        if controls.logging == True:
            #print "writing file"
            #print dataString
            controls.dataFile.write(dataString)
            
        if controls.displayGraphRemote == True:
            dataSendString = "%s, %s, %s, %s\n" % (str(timeStamp), str(PVal), str(CVal), str(controls.collecting))
            controls.sock.sendall(dataSendString)
        if self.MFC:
            return CVal, PVal, FVal, timeStamp
        else:
            return CVal, PVal, timeStamp
    
    def selectionMatrix(self, controls, CVal, PVal):
        if isinstance(controls.sensors.Pressure.triggerValues, list):
            if controls.settings["collection_control"] == "c" and CVal >= controls.sensors.CO2.triggerValues[0] and controls.collecting==0:
                print "collecting"
                controls.collecting = controls.sensors.CO2.triggerValues[0]
            
            elif controls.settings["collection_control"] == "c" and CVal <= controls.sensors.CO2.triggerValues[1] and controls.collecting!=0:
                print "stopped collecting"
                controls.collecting = 0
            
            elif controls.settings["collection_control"] == "p" and PVal >= controls.sensors.Pressure.triggerValues[0] and controls.collecting==0:
                print "Started pump collecting"
                controls.collecting = controls.sensors.Pressure.triggerValues[0]
            
            elif controls.settings["collection_control"] == "p" and PVal <= controls.sensors.Pressure.triggerValues[1] and controls.collecting!=0:
                print "stopped pump collecting"
                controls.collecting = 0
            
            else:
                #print "continue as is"
                pass
            
        else:
            if controls.settings["collection_control"] == "c" and CVal >= controls.sensors.CO2.triggerValues:
                print "collecting"
                controls.collecting = controls.sensors.CO2.triggerValues
            
            elif controls.settings["collection_control"] == "p" and PVal >= controls.sensors.Pressure.triggerValues:
                print "collecting"
                controls.collecting = controls.sensors.Pressure.triggerValues
            
            else:
                controls.collecting = 0
        return controls
        

class CO2_sensor: #designed for things like CO2, flow or pressure etc   HOW TO MERGE THE SENSOR TYPES?????
    def __init__(self, connection, samplePeriod = 0.2):
        self.connection = connection
        self.samplePeriod = samplePeriod
        self.triggerValues = 3.2
        
        self.commLink = self.initialiseConnection()

    def initialiseConnection(self):
        print r"%s" % self.connection
        conn = Serial(self.connection, writeTimeout = 3)    #9600 baud
        #conn = Serial("/dev/ttyUSB0", writeTimeout = 3)    #9600 baud
        print "starting CO2 connection"
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

class Flow_sensor: #Should be rolled into CO2_sensor and just called input sensor
    def __init__(self, commLink, samplePeriod = 0.2):       # Feed in the commlink from Pressure sensor - uses the same board
        
        self.totalVolume = 0    # sccm
        self.lastFlow = 0
        self.lastTime = 0
        self.currentFlow = 0
        self.currentTime = 0
        
        self.samplePeriod = samplePeriod
        
        self.commLink = commLink
        print "trying outside of IC:"
        self.commLink.write('F')
        check = self.commLink.readline()
        print check
        if check == -1:
            print "no MFC detected - cannot get value"
            self.Available = False
        else:
            self.Available = True

    def getReading(self):
        if self.Available == False:
            return -1
        self.commLink.write('F')
        #print "written r to Arduino"
        Flow = float(self.commLink.readline() )
        #print "got pressure"
        return Flow
    
    def collectedVolume(self, totalBreath, collecting):
        #if collectingStatus == "selected breath" or collectingStatus != 0:
        if totalBreath == True and collecting != 0:    
            Vol = ((self.currentFlow+self.lastFlow)/120.0)*(self.currentTime-self.lastTime)      # Flow measured in ml/min, 120 = 2*60
            self.totalVolume += Vol
        elif totalBreath == False:
            Vol = ((self.currentFlow+self.lastFlow)/120.0)*(self.currentTime-self.lastTime)      # Flow measured in ml/min, 120 = 2*60
            self.totalVolume += Vol

        self.lastTime = self.currentTime
        self.lastFlow = self.currentFlow
        return self.totalVolume
    
    def reset(self, startTime):
        self.lastTime = startTime
        self.currentTime = startTime
        self.lastFlow = 0
        self.totalVolume = 0

class Pressure_sensor: #Should be rolled into CO2_sensor and just called input sensor
    def __init__(self, connection, samplePeriod = 0.2):
        self.connection = connection
        self.samplePeriod = samplePeriod
        self.triggerValues = 350
        
        self.commLink = self.initialiseConnection()
        print "trying outside of IC:"
        self.commLink.write('P')
        print self.commLink.readline()

    def initialiseConnection(self):
        print "starting Pressure connection"
        conn = Serial(self.connection, 9600, timeout = 3)
        time.sleep(1)
        conn.write('P')
        print conn.readline()
        print"initialised Pressure"
        return conn

    def getReading(self):
        self.commLink.write('P')
        #print "written r to Arduino"
        pressure = float( self.commLink.readline() )
        #print "got pressure"
        return pressure