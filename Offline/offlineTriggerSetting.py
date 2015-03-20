#!/usr/bin/env python

from matplotlib import pyplot as plt
import os
import re
import numpy


def smooth(x, window_len=9,window='blackman'):   # 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
    #if x.ndim != 1:
    #    raise ValueError, "smooth only accepts 1 dimension arrays."

    if len(x) < window_len: #.size
        raise ValueError, "Input vector needs to be bigger than window size."

    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"

    
    print "got here here here"
    s=numpy.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=numpy.ones(window_len,'d')
    else:
        w=eval('numpy.'+window+'(window_len)')

    y=numpy.convolve(w/w.sum(),s,mode='valid')
    print "length of the returned obj: %d" % len(y)
    gate1 = (window_len-1)/2
    gate2 = -((window_len-1)/2)
    print "gates are: %d, %d" % (gate1, gate2)
    print "length of returned obj = %d" % len(y[gate1: gate2])
    return y[gate1: gate2]

def peakDetection(data, timeS):
    
    minProximity = 1.5   #closest the next peak can be in dataset in seconds, 1.55 sec either side of 
    
    #peaksC = []
    #peaksP = []
    #troughsC = []
    #troughsP = []
    
    extremes = [[],[]] #peaks, troughs
    
    for i, d in enumerate(data):
        try:
            if d > data[i-1] and d > data[i+1]:
                extremes[0].append([d, timeS[i], i])    #peaks
                #peaksC.append([d, i])
            
            if d < data[i-1] and d < data[i+1]:
                extremes[1].append([d, timeS[i], i])    #troughs
                #troughsC.append([d, i])

        except IndexError:
            pass
    
    outputGroups = []
    
    
    for group in extremes:      # should throw away any close peaks - group is either peak or trough
        outGroup = []
        
        for p, point in enumerate(group):
            try:
                
                gap = group[p][1] - group[p-1][1]
                #gap = point[2] - group[p-1][2]
                print "gap = %f " % gap
                if gap > minProximity or gap < 0:
                    outGroup.append(point[0:2])
            
            except IndexError:
                outGroup.append(point[0:2])     #point is [data, time, index from overall list]
                pass
        outputGroups.append(outGroup)
    
    averages=[averageValueFiltered([p[0] for p in outputGroups[0]]),averageValueFiltered([p[0] for p in outputGroups[1]])] #average peak, average trough
    
    return outputGroups, averages     #returns a list of 2 lists, each of which contains a list of [data, time], and average[peak, trough]
    
def averageValueFiltered(data):
    mean = numpy.mean(data)
    stddev = numpy.std(data)
    print "mean is: %f" % mean
    print "std dev is: %f" % stddev
    finalData = []
    for d in data:
        if d < mean + stddev and d > mean - stddev:
            finalData.append(d)
    
    return numpy.mean(finalData)


def setTriggerValues(Limits):
    
    interLimitRange = Limits[0]-Limits[1] #peak - trough
    
    Trigger = Limits[1] + interLimitRange/2 #CUrrently at 50% of range... because it is an illustration
    
    return Trigger
    
    
class dP:   #data point
    def __init__(self, tS, P, C, Coll): #time, pressure, CO2, collecting
        self.tS = tS
        self.p = P
        self.c = C
        self.coll = Coll

def getLatestData():
    
    fileLoc = r"C:\Users\simon.kitchen\Documents\Software\Sandbox\Python\Test_rig\Sampling\PiDatafiles"
    #fileLoc = r"\\OWLSERV03\NewSTOUT\Server\temp\SK\LuCID\Pump and traps\trap flow test results complete"
    
    fList = []
    for files in os.walk(fileLoc):
        for filenames in files:
            for filename in filenames:
                if re.match("142[0-9]+\.txt", filename):   #if filename.find("trap") > -1 and filename.find("txt") > -1:  #if filename.find(re.search("trap[0-9]") > -1:
                    fList.append(filename)
                    #print filename

    newestStamp = 0
    for fileName in fList:
        timeStamp = float(fileName.strip(r".txt"))
        if timeStamp > newestStamp:
            newestStamp = timeStamp
    
    dataFile = open(fileLoc + '\\' + str(int(newestStamp)) + ".txt")
    allData = dataFile.read()
    #print allData
    allData.strip('\n')
    allData.strip('')
    dataGroups = allData.split('\n')
    #dataGroups = dataGroups.strip('')
    
    indData = []
    firstPoint = True
    for DG in dataGroups:
        if DG == '':
            pass
        else:
            DG1 = DG.strip('')
            DG2 = DG1.split(', ')
            #print DG2
            
            if firstPoint == True:
                startTime = float(DG2[0])
                firstPoint = False
            if float(DG2[0]) - startTime > 50:
                break
            indData.append(dP(float(DG2[0])- startTime, float(DG2[1]), float(DG2[2]), bool(DG2[3])))
    
    return indData

def plotData(Data, extremeCO2, extremePressure, CO2Triggers, PressureTriggers):
    
    timeData = []
    pressureData = []
    CO2Data = []
    for d in Data:
        timeData.append(d.tS)
        pressureData.append(d.p)
        CO2Data.append(d.c)
    
    fig, axCO2 = plt.subplots()
    plt.xlabel("time  s")
    axPressure = plt.twinx()
    
    axCO2.set_ylabel("CO2 %", color = 'b')
    axPressure.set_ylabel("Pressure Pa", color = 'r')
    axCO2.plot(timeData, CO2Data, 'b-')
    
    axCO2.plot([timeData[0], timeData[-1]], [CO2Triggers, CO2Triggers], 'b-')
    axCO2.plot([pont[1] for pont in extremeCO2[0]], [pont[0] for pont in extremeCO2[0]], 'b^')  #EXTREMEco2[PEAK/TROUGH][LIST OF POINTS][data, time]
    axCO2.plot([pont[1] for pont in extremeCO2[1]], [pont[0] for pont in extremeCO2[1]], 'bv')
    
    
    
    
    axPressure.plot(timeData, pressureData, 'r-')
    
    axPressure.plot([timeData[0], timeData[-1]], [PressureTriggers, PressureTriggers], 'r-')
    axPressure.plot([pont[1] for pont in extremePressure[0]], [pont[0] for pont in extremePressure[0]], 'r^')
    axPressure.plot([pont[1] for pont in extremePressure[1]], [pont[0] for pont in extremePressure[1]], 'rv')
    
    plt.show()

    
if __name__ == '__main__':
    data = getLatestData()
    print "ts is: %d, te is: %d" % (data[0].tS, data[-1].tS)
    totalTime = data[-1].tS - data[0].tS
    print "total time was: %f " % totalTime
    print "samples: %d " % len(data)
    
    timeS = []
    CO2Data = []
    PressureData = []
    for d in data:
        CO2Data.append(d.c)
        timeS.append(d.tS)
        PressureData.append(d.p)
    smoothedCO2Data = smooth(CO2Data)
    smoothedPressureData = smooth(PressureData)

    # extremeCO2 is a list of lists of lists:[peak/trough][item][data, time]
    extremeCO2, CO2Limits = peakDetection(smoothedCO2Data, timeS)          
    extremePressure, PressureLimits = peakDetection(smoothedPressureData, timeS)
    
    CO2Triggers = setTriggerValues(CO2Limits)
    PressureTriggers = setTriggerValues(PressureLimits)
    
    #extremeCO2 = peakDetection(CO2Data, timeS)          
    #extremePressure = peakDetection(PressureData, timeS)
    
    
    #setTriggerValues(data)
    
    plotData(data, extremeCO2, extremePressure, CO2Triggers, PressureTriggers)