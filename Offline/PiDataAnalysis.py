#!/usr/bin/env python

# Deprecated - now use PiDataAnalysisSmoothed - incorporates latest updates.

from matplotlib import pyplot as plt
import os
import re

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
            print DG2
            
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
    
    fig, axCO2 = plt.subplots()
    plt.xlabel("time  s")
    axPressure = plt.twinx()
    
    axCO2.set_ylabel("CO2 %", color = 'b')
    axPressure.set_ylabel("Pressure Pa", color = 'r')
    axCO2.plot(timeData, CO2Data, 'b-')
    axPressure.plot(timeData, pressureData, 'r-')
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