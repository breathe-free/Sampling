#!/usr/bin/env python

#import Collector
#import sensorPoll

import time
from collections import deque

import matplotlib.pyplot as plt
import matplotlib.animation as animation

class collectionTimeExpiredException:
    def __init__(self):
        pass
    

class graphing:
    def __init__(self):
        maxLen = 100
        self.CO2Trace = deque([0.0]*maxLen)
        self.pressureTrace = deque([0.0]*maxLen)
        self.maxLen = maxLen
        self.start_time = time.time()

  # add to buffer
    def addToBuf(self, buf, val):
        if len(buf) < self.maxLen:
            buf.append(val)                     #### why not appendleft???
        else:
            buf.pop()
            buf.appendleft(val)

  # add data
    def add(self, data):
        assert(len(data) == 2)
        self.addToBuf(self.CO2Trace, data[0])
        self.addToBuf(self.pressureTrace, data[1])
    
    def getAxisLimits(self, controls):
        time_start = time.time()
        tempData = []
        CO2Data = []
        PressureData = []
        for i in range(10*controls.secDivision):
            print "looping for calibration: %d" % i
            CO2, Pressure, time_stamp = controls.sensors.getReadings(controls, logging = False)
            tempData.append([time_stamp - time_start, CO2, Pressure])
            CO2Data.append(CO2)
            PressureData.append(Pressure)
            timeToWait = ((float(i+1)/float(controls.secDivision))-(time.time() - time_start))
            if timeToWait <= 0:
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
        
    
    
    # update plot
    def update(self, frameNum, traceCO2, tracePressure, controls):
        

        if time.time() - controls.time_start >= controls.test_length*controls.secDivision: ##exit case 1
            print "exiting because of time run out"
            controls.dataFile.close()
            print "now at pump"
            controls.collecting = 0
            controls.sample_pump.power_switch(controls.collecting)
            raise collectionTimeExpiredException()
        
        #if controls.
        
        try:
            CO2, Pressure, time_stamp = controls.sensors.getReadings(controls)

            controls.counter = controls.counter + 1
            print "counter: %d" % controls.counter
            TS = ((controls.counter+1.0)/controls.secDivision) - (time.time()-controls.time_start)
            if TS <= 0:
                TS = 0
            time.sleep(TS)
            data = []
            data.append(CO2)
            data.append(Pressure)
            
            # print data
            if(len(data) == 2):
                self.add(data)
                traceCO2.set_data(range(self.maxLen), self.CO2Trace)
                tracePressure.set_data(range(self.maxLen), self.pressureTrace)
        except KeyboardInterrupt:
            controls.dataFile.close()
            print('exiting')

        return traceCO2

    def runGraphingLoop(self, controls):
        
        
        
        
        #CO2Min, CO2Max, pressureMin, PressureMax  = self.getAxisLimits(controls)
        
        
        print 'plotting data...'

        # set up animation
        fig, axCO2 = plt.subplots()
        plt.xlim(0, 100)
        #plt.ylim(CO2Min, CO2Max)   #Neat way of setting axis limits! -- Check functionality
        plt.ylim(0, 5)
        
        
                                    #axPressure = plt.axes(xlim=(0, 100), ylim=(yMin, yMax))
        plt.xlabel("time s*5")
        axPressure = plt.twinx()
        #plt.ylim(PressureMin, PressureMax)
        plt.xlim(0, 100)
        plt.ylim(-1000, 3000)
        axCO2.set_ylabel('CO2 %', color='b')
        traceCO2, = axCO2.plot([], [], 'b-')            # yes the commas need to be there... don't ask why.
        axPressure.set_ylabel('Pressure Pa', color='r')
        tracePressure, = axPressure.plot([], [], 'r-')  # yes the commas need to be there... don't ask why.
        
        controls.time_start = time.time()
        controls.counter = 0
        cycles = controls.test_length*controls.secDivision
        loopTime = 1000/controls.secDivision
        
        try:
            anim = animation.FuncAnimation(fig, controls.Grapher.update, frames = cycles,  # interval = loopTime,
                                           fargs=(traceCO2, tracePressure, controls)) #, blit=True)
        except collectionTimeExpiredException:
            pass
        
        print "showing plot???"
        # show plot
        plt.show()
        
        # clean up
        analogPlot.close()

        print('exiting from here.')

    # clean up
    def close(self):
        # serial tidy
        pass

if __name__ == '__main__':
    
    pass