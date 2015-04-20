#!/usr/bin/env python

from serial import Serial
import time

class sensorList:
    def __init__(self, CO2Ad, PressureAd, MFC):
        self.CO2 = CO2_sensor(CO2Ad)
        self.pressure = Pressure_sensor(PressureAd)
        self.MFC = MFC
        if self.MFC:
            self.Flow = Flow_sensor(self.pressure.comm_link)
  
    def getReadings(self, controls):
        PVal = self.pressure.getReading()
        #print "got pressure"
        CVal = self.CO2.getReading()
        #print "got CO2"
        if self.MFC:
            FVal = self.Flow.getReading()
        time_stamp = time.time()
        
        controls = self.selectionMatrix(controls,CVal, PVal)
        
        if controls.control_pump_with_triggers == True:
            #print "now at pump"
            if controls.collecting != 0:
                
                controls.sample_pump.power_switch("on")
            else:
                controls.sample_pump.power_switch("off")
        
        if self.MFC:
            self.Flow.currentFlow = FVal
            self.Flow.current_time = time_stamp
            dataString = "%s, %s, %s, %s, %s\n" % (str(time_stamp), str(PVal), str(CVal), str(FVal), str(controls.collecting))
        else:
            dataString = "%s, %s, %s, %s\n" % (str(time_stamp), str(PVal), str(CVal), str(controls.collecting))
        if controls.logging == True:
            #print "writing file"
            #print dataString
            controls.dataFile.write(dataString)
            
        if controls.display_graph_remote == True:
            dataSendString = "%s, %s, %s, %s\n" % (str(time_stamp), str(PVal), str(CVal), str(controls.collecting))
            controls.sock.sendall(dataSendString)
        if self.MFC:
            return CVal, PVal, FVal, time_stamp
        else:
            return CVal, PVal, time_stamp
    
    def selectionMatrix(self, controls, CVal, PVal):
        if isinstance(controls.sensors.pressure.trigger_values, list):
            if controls.settings["collection_control"] == "c" and CVal >= controls.sensors.CO2.trigger_values[0] and controls.collecting==0:
                print "collecting"
                controls.collecting = controls.sensors.CO2.trigger_values[0]
            
            elif controls.settings["collection_control"] == "c" and CVal <= controls.sensors.CO2.trigger_values[1] and controls.collecting!=0:
                print "stopped collecting"
                controls.collecting = 0
            
            elif controls.settings["collection_control"] == "p" and PVal >= controls.sensors.pressure.trigger_values[0] and controls.collecting==0:
                print "Started pump collecting"
                controls.collecting = controls.sensors.pressure.trigger_values[0]
            
            elif controls.settings["collection_control"] == "p" and PVal <= controls.sensors.pressure.trigger_values[1] and controls.collecting!=0:
                print "stopped pump collecting"
                controls.collecting = 0
            
            else:
                #print "continue as is"
                pass
            
        else:
            if controls.settings["collection_control"] == "c" and CVal >= controls.sensors.CO2.trigger_values:
                print "collecting"
                controls.collecting = controls.sensors.CO2.trigger_values
            
            elif controls.settings["collection_control"] == "p" and PVal >= controls.sensors.pressure.trigger_values:
                print "collecting"
                controls.collecting = controls.sensors.pressure.trigger_values
            
            else:
                controls.collecting = 0
        return controls
        

class CO2_sensor: #designed for things like CO2, flow or pressure etc   HOW TO MERGE THE SENSOR TYPES?????
    def __init__(self, connection, samplePeriod = 0.2):
        self.connection = connection
        self.samplePeriod = samplePeriod
        self.trigger_values = 3.2
        
        self.comm_link = self.initialise_connection()

    def initialise_connection(self):
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
        self.comm_link.write('z\r\n')
        readString = self.comm_link.readline()
        readString = readString.strip()
        readString = readString.split()
        pp105 = float(readString[1]) # ppm/10! - not ppm
        CO2percent = pp105/1000
        return CO2percent

class Flow_sensor: #Should be rolled into CO2_sensor and just called input sensor
    def __init__(self, comm_link, samplePeriod = 0.2):       # Feed in the commlink from Pressure sensor - uses the same board
        
        self.totalVolume = 0    # sccm
        self.lastFlow = 0
        self.lastTime = 0
        self.currentFlow = 0
        self.current_time = 0
        
        self.samplePeriod = samplePeriod
        
        self.comm_link = comm_link
        print "trying outside of IC:"
        self.comm_link.write('F')
        check = self.comm_link.readline()
        print check
        if check == -1:
            print "no MFC detected - cannot get value"
            self.Available = False
        else:
            self.Available = True

    def getReading(self):
        if self.Available == False:
            return -1
        self.comm_link.write('F')
        #print "written r to Arduino"
        Flow = float(self.comm_link.readline() )
        #print "got pressure"
        return Flow
    
    def collectedVolume(self, totalBreath, collecting):
        #if collectingStatus == "selected breath" or collectingStatus != 0:
        if totalBreath == True and collecting != 0:    
            Vol = ((self.currentFlow+self.lastFlow)/120.0)*(self.current_time-self.lastTime)      # Flow measured in ml/min, 120 = 2*60
            self.totalVolume += Vol
        elif totalBreath == False:
            Vol = ((self.currentFlow+self.lastFlow)/120.0)*(self.current_time-self.lastTime)      # Flow measured in ml/min, 120 = 2*60
            self.totalVolume += Vol

        self.lastTime = self.current_time
        self.lastFlow = self.currentFlow
        return self.totalVolume
    
    def reset(self, start_time):
        self.lastTime = start_time
        self.current_time = start_time
        self.lastFlow = 0
        self.totalVolume = 0

class Pressure_sensor: #Should be rolled into CO2_sensor and just called input sensor
    def __init__(self, connection, samplePeriod = 0.2):
        self.connection = connection
        self.samplePeriod = samplePeriod
        self.trigger_values = 350
        
        self.comm_link = self.initialise_connection()
        print "trying outside of IC:"
        self.comm_link.write('P')
        print self.comm_link.readline()

    def initialise_connection(self):
        print "starting Pressure connection"
        conn = Serial(self.connection, 9600, timeout = 3)
        time.sleep(1)
        conn.write('P')
        print conn.readline()
        print"initialised Pressure"
        return conn

    def getReading(self):
        self.comm_link.write('P')
        #print "written r to Arduino"
        pressure = float( self.comm_link.readline() )
        #print "got pressure"
        return pressure