#!/usr/bin/env python

import time

def getReadings(controls, logging = True):          # this should be moved into Sensors as a function within sensorList
    PVal = controls.sensors.Pressure.getReading()
    print "got pressure"
    CVal = controls.sensors.CO2.getReading()
    print "got CO2"
    timeStamp = time.time()
    if controls.controlSelection == "c" and CVal >= controls.sensors.CO2.triggerValue:
        print "collecting"
        controls.collecting = controls.sensors.CO2.triggerValue

    elif controls.controlSelection == "p" and PVal >= controls.sensors.Pressure.triggerValue:
        print "collecting"
        controls.collecting = controls.sensors.Pressure.triggerValue

    else:
        controls.collecting = 0
    
    if controls.collectionRun == True:
        print "now at pump"
        controls.myPump.turnOnOff(controls.collecting)
    
    if logging == True:
        print "writing file"
        controls.dataFile.write("%s, %s, %s, %s\n" % (str(timeStamp), str(PVal), str(CVal), str(controls.collecting)))
    if controls.displayGraphRemote == True:
        pass        # insert Richard's code here!
    
    return CVal, PVal, timeStamp