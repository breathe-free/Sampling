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
#import csv     # Nice idea, not currently executed

DEFAULT_SETTINGS = {
    "tube_id":                  None
    "sample_date_time":         None
    "calibration_time":         20,
    "sample_collection_time":   2000,
    "collection_control":       "p",
    "auto_triggers":            True,
    "blank_capture":            False,
    "total_breath":             False,
    "collection_rate":          500,
    "collection_limit":         500,
    "filename":                 "dataFile",
    "capture_window": {
        "start": { 
            "percent":  50,
            "gradient": "rising"
        },
        "end": { 
            "percent":  50,
            "gradient": "falling"
        },
    }
}

LOCAL_SETTINGS = {
    "CO2_address":          "/dev/ttyUSB0",
    "pressure_address":     "/dev/ttyACM0",
    "pump_address":         "/dev/ttyUSB1",
    "poll_rate":            5,
    "default_pump_voltage": 24,
    "default_pressure_trigger": 500,
    "default_CO2_trigger": 2.5,
}


class Control:
    #code
    def __init__(self):
        self.MFC = True     # Flag if whether MFC is attached or not
        self.volume_collection_limit = 50
        self.settings = DEFAULT_SETTINGS
        self.local_settings = LOCAL_SETTINGS

        self.sensors = Sensors.sensorList(LOCAL_SETTINGS["CO2_address"],
                                          LOCAL_SETTINGS["pressure_address"],
                                          self.MFC,
                                          )
        self.sensors.CO2.trigger_values = [DEFAULT_SETTINGS["default_CO2_trigger"],
                                           DEFAULT_SETTINGS["default_CO2_trigger"]
                                           ]
        self.sensors.pressure.trigger_values = [DEFAULT_SETTINGS["default_pressure_trigger"],
                                                DEFAULT_SETTINGS["default_pressure_trigger"]
                                                ]
        self.sample_pump = Pumps.output_controller(LOCAL_SETTINGS["pump_address"],
                                                   LOCAL_SETTINGS["default_pump_voltage"]
                                                   )
        
        self.logging = True            #save CO2, Pressure and other data to txt file?
        self.control_pump_with_triggers = True      #Run the sample collection pump when the gating algorithm returns True?
        self.CO2_draw_through = False      #Run the pump constantly to draw air through the CO2 sensor?
        self.display_graph_local = False  #Plots the graph in a matplotlib animation locally
        self.display_graph_remote = True  #Writes CO2, Pressure and other data to a socket that can be picked up by
        #self.totalBreath = False #Pump runs constantly, however measures the same volume of breath as a selected breath would
                                #"collect". If you want a fixed volume of air leave this false and set CO2_draw_through = True.
                                            # Richard's web interface

    def close(self):
        self.sensors.CO2.comm_link.close()
        self.sensors.pressure.comm_link.close()
        self.sample_pump.comm_link.close()
    
    def Runner(self, remote_comms):
        self.sock = remote_comms.sock
        if self.settings["total_breath"]:
            self.control_pump_with_triggers = False
        if self.settings["blank_capture"]:
            self.control_pump_with_triggers = False
        self.sample_pump.frequency_sweep()
        self.time_start = time.time()
        FileTime = self.time_start
        timeS = [self.time_start]
        self.collecting = 0
        #print "time start is: %s" % self.time_start
        
        dataStore = os.path.join(os.path.dirname(__file__), "..", "datafiles")
        setupFileName = dataStore+"/"+str(int(FileTime))+self.settings["filename"]+"CalibrationData.txt"
        self.dataFile = open(setupFileName, 'w')
        #json.dump(self.settings, self.dataFile)
        #self.dataFile.write("\n Calibrating Data Starts Here \n")
        
        #Set up sampler settings and get breathing pattern:
        print "Now collecting for trigger calculation"
        statusHolder = self.control_pump_with_triggers       # ensure the pump doesn't run during this phase and collect the wrong sample
        self.control_pump_with_triggers = False

        remote_comms.change_state(remote_comms.STATES.CALIBRATING)
        self.localLoop(self.settings["calibration_time"], remote_comms)    #callibration time, 30sec should allow 5 breaths, a good average
        self.dataFile.close()
        self.control_pump_with_triggers = statusHolder       #turn pump back on to previous settings
        remote_comms.change_state(remote_comms.STATES.ANALYSING)
        trigger_cal = TriggerSetting.TriggerCalcs()
        all_trigger_vals = trigger_cal.calculate(setupFileName,
                                                 self.settings["capture_window"]["start"]["percent"],
                                                 self.settings["capture_window"]["end"]["percent"]
                                                 )
        self.sensors.CO2.trigger_values = all_trigger_vals[0]
        self.sensors.pressure.trigger_values = all_trigger_vals[1]
        print type(all_trigger_vals)
        #self.dataFile.write("\n Trigger values for this collection run are: \n")
        if isinstance(all_trigger_vals[0], list):
            print "*******************************************"
            for iii in range(2):
                print iii
                print "CO2 Trigger Val is: %f" % all_trigger_vals[iii][0]
                print "Pressure Trigger Val is: %f" % all_trigger_vals[iii][1]
                
        else:
            print"##############################################"
            print "CO2 Trigger Val is: %f" % all_trigger_vals[0]
            print "Pressure Trigger Val is: %f" % all_trigger_vals[1]
        
        settingFileName = dataStore+"/"+str(int(FileTime))+self.settings["filename"]+"RunSettings.txt"
        self.settingFile = open(settingFileName, 'w')
        json.dump(self.settings, self.settingFile)
        json.dump(all_trigger_vals, self.settingFile)
        self.settingFile.close()
        
        dataFileName = dataStore+"/"+str(int(FileTime))+self.settings["filename"]+"CollectionData.txt"
        self.dataFile = open(dataFileName, 'w')
        if self.CO2_draw_through == True:
            #print "turning pump on"
            self.sample_pump.power_switch("on")
            time.sleep(1)
        if self.settings["total_breath"]:
            self.sample_pump.power_switch("on")
        if self.settings["blank_capture"]:
            self.sample_pump.power_switch("on")
            
        print "measurement loop"
        self.dataFile.write("\n Collection Data Starts Here \n")
        remote_comms.change_state(remote_comms.STATES.COLLECTING)
        if self.display_graph_local == True:
            self.Grapher = RTP.graphing()
            self.Grapher.runGraphingLoop(self)
        elif self.display_graph_local == False:
            self.localLoop(self.settings["sample_collection_time"], remote_comms)
            
        print "finished collecting"
        self.sample_pump.power_switch("off")
        self.dataFile.close()
        remote_comms.change_state(remote_comms.STATES.WAITING)
        print "done!!!"
        
    def localLoop(self, test_length, remote_comms):
        self.time_start = time.time()
        counter = 0
        self.collectionLimitReached = False
        
        #while time.time()-self.time_start <= test_length and not self.collectionLimitReached:
        if self.MFC:
            print "MFC is True"
            self.sensors.Flow.reset(self.time_start)
            current_volume = 0
            time_stamp = self.time_start
            while time_stamp-self.time_start <= test_length and current_volume < self.settings["collection_limit"]:
                CO2, Pressure, Flow, time_stamp = self.sensors.getReadings(self)
                current_volume = self.sensors.Flow.collectedVolume(self.settings["total_breath"], self.collecting)
                counter = counter + 1
                if counter%5.0 == 0:
                    remote_comms.set_completion(test_length, self.settings["collection_limit"],
                                                self.time_start, time_stamp,
                                                current_volume
                                                )
                commands = remote_comms.checkCommands(self)
                if commands is not None and commands.find("stopsampling") >= 0:
                    break
                ts = float(counter)/LOCAL_SETTINGS["poll_rate"] - (time.time()-self.time_start)
                if ts < 0:
                    ts = 0
                time.sleep(ts)
            
            tt = (time.time()-self.time_start)
            print "Total test time was: %f" % tt
            vv = self.sensors.Flow.collectedVolume(self.settings["total_breath"], self.collecting)
            print "Total test collection volume was: %f" % vv
            print "so which one stopped it: %f, %f" %(test_length, self.settings["collection_limit"])
        else:
            print "MFC is False"
            while time.time()-self.time_start <= test_length:
                CO2, Pressure, time_stamp = self.sensors.getReadings(self)
                counter = counter + 1
                commands = remote_comms.checkCommands(self)
                if commands is not None and commands.find("stopsampling") >= 0:
                    break
                TS = float(counter)/LOCAL_SETTINGS["poll_rate"] - (time.time()-self.time_start)
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
        
        self.state = None
        self.change_state(self.STATES.INITIALISING)
    
    def receive(self):
        # Act as an iterator.  Sometimes >1 message will have accumulated on the
        # socket by the time we come to read it.
        # Yield either None (if nothing received, buffer empty) or json decode line by line.
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
    
    def set_completion(self, time_limit, volume_limit, start_time, current_time, current_volume):
        by_time, by_volume = self.support.calculateCurrentCompletion(time_limit, volume_limit, start_time, current_time, current_volume)
        self.collection_completion = {
            "volume":  min(100, by_volume),
            "time":    min(100, by_time),
        }
        self.emit_state(
            collection_completion = self.collection_completion,
        )
    
    def close(self):
        self.sock.close()
    
    def checkCommands(self, controls):        #sort of equivalent to run in Richard's main function
        # read from sock
        received = self.receive().next()
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
                controls.settings = received['settings']
                return "startsampling"

            elif do_what == "request_state":
                self.emit_state()
            
            elif do_what == "request_settings_current":
                self.emit_state(settings=controls.settings)
            
            elif do_what == "apply_settings_default":
                controls.settings = self.support.load_settings("default")
                self.emit_state(settings=controls.settings, message="Loaded default settings.", severity="info")
            
            elif do_what == "apply_settings_user":
                controls.settings = self.support.load_settings("user")
                if controls.settings == -1:
                    controls.settings = self.support.load_settings("default")
                    self.emit_state(settings=controls.settings, message="WARNING: User settings not available, have loaded default settings instead.", severity="warning")
                else:
                    self.emit_state(settings=controls.settings, message="Loaded user settings.", severity="info")
            
            elif do_what == "save_settings":
                settings = received['settings']
                self.support.saveSettings(settings)
                self.emit_state(settings=controls.settings, message="Saved user settings.", severity="info")

class Support_Functions:
    def __init__(self):
        pass
    def saveSettings(self, settings):
        with open("UserDefinedSettings.txt", "w") as outfile:
            json.dump(settings, outfile)            #save to user settings file (overwrite)
    
    def load_settings(self, source):
        if source == "user":
            try:
                with open("UserDefinedSettings.txt", "r") as infile:
                    return json.load(infile)            #load from user settings file (overwrite)
            except:
                print "Print no available User Settings file, have loaded nothing instead"
                return -1

        elif source == "default":
            return DEFAULT_SETTINGS
        else:
            return DEFAULT_SETTINGS
    
    def calculateCurrentCompletion(self, time_limit, volume_limit, start_time, current_time, current_volume):
        timePercentage = ((current_time-start_time)*100)/time_limit
        volumePercentage = (current_volume*100)/volume_limit
        return timePercentage, volumePercentage


def mainProgram(remoteControl = True):
    sampler_control = Control()
    sampler_comms = Communications(sampler_control)
    if not sampler_control.sensors.Flow.Available:
        sampler_comms.emit_state(message="WARNING: No MFC connected", severity="warning")
    
    #try:
    while True:
        try:
            print "waiting for response from web interface"
            sampler_comms.change_state(sampler_comms.STATES.WAITING)
            while remoteControl:
                #sampler_comms loop until got a start command
                commString = sampler_comms.checkCommands(sampler_control)
                if commString is not None and "startsampling" in commString: #commString.find("startsampling") >= 0:
                    print "Heard something"
                    break
                time.sleep(0.5)
        except KeyboardInterrupt:
            #print "Keyboard used to interrupt - do I need to close something here?"
            sampler_control.close()
            sampler_comms.close()
            sys.exit()
    
        sampler_control.Runner(sampler_comms)
        if not remoteControl:
            noInput = True
            while noInput == True:
                userInput = raw_input("Collection cycle complete, type r to repeat, or q to quit: ")
                if userInput == 'r':
                    noInput = False
                elif userInput == 'q':
                    sampler_control.close()
                    sampler_comms.close()
                    sys.exit()
                else:
                    print "invalid arguement, please enter r or q"
    #except:
    #    sampler_comms.emit_state(message="ERROR: Control software has irrecoverably errored. Please restart the\ncontroller with the line 'python Controller.py'", severity="error")

if __name__ == '__main__':

    remoteControl = True
    mainProgram(remoteControl)