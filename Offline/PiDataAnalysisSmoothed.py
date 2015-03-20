#!/usr/bin/env python

from matplotlib import pyplot as plt
import os
import re
import numpy

class dP:   #data point
    def __init__(self, tS, P, C, Coll): #time, pressure, CO2, collecting
        self.tS = tS
        self.p = P
        self.c = C
        self.coll = Coll




    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    """
def smooth(x,window_len=11,window='blackman'):   # 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
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
    return y


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
            #if float(DG2[0]) - startTime > 50:
             #   break
            indData.append(dP(float(DG2[0])- startTime, float(DG2[1]), float(DG2[2]), bool(DG2[3])))
    
    return indData

def plotData(Data):
    
    timeData = []
    pressureData = []
    CO2Data = []
    for d in Data:
        timeData.append(d.tS)
        pressureData.append(d.p)
        CO2Data.append(d.c)
    
    CO2DataSmoothed = smooth(CO2Data)
    pressureDataSmoothed = smooth(pressureData)
    fig, axCO2 = plt.subplots()
    plt.xlabel("time  s")
    axPressure = plt.twinx()
    print " now im trying to do this here"
    print len(timeData)
    print len(CO2DataSmoothed)
    print len(pressureDataSmoothed)
    
    axCO2.set_ylabel("CO2 %", color = 'b')
    axPressure.set_ylabel("Pressure Pa", color = 'r')
    axCO2.plot(timeData, CO2DataSmoothed[:-10], 'b-')
    axPressure.plot(timeData, pressureDataSmoothed[:-10], 'r-')
    plt.show()

    
def plotDataOld(Data):
    
    plt.figure(0)
    plt.xlabel("time s")
    plt.ylabel("Pressure Pa")
    
    xData = []
    yData = []
    for d in Data:
        xData.append(d.tS)
        yData.append(d.p)
    
    plt.plot(xData, yData)
    
    plt.figure(1)
    plt.xlabel("time s")
    plt.ylabel("CO2 %")
    
    xData = []
    yData = []
    for d in Data:
        xData.append(d.tS)
        yData.append(d.c)
    
    plt.plot(xData, yData)
    
    plt.show()
    
if __name__ == '__main__':
    data = getLatestData()
    
    totalTime = data[-1].tS - data[0].tS
    
    print "total time was: %f " % totalTime
    print "samples: %d " % len(data)
    plotData(data)