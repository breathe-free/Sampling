# Sampling

Online:

This code takes readings from a number of different sensors; including differential pressure, CO2 concentration and mass flow.
It uses an initial calibration period to set maximum and minimum values for an individual before using these to determine gating values
at which to turn the sample collection pump on or off.

Using the default mode the data from the sensors and the pump status is simultaneously saved to a local data file and also written to a unix socket to enable
(near) real-time visualisation of the individual's breathing pattern in a web browser (breathe-see).

By changing flags in Controller.py the data can be displayed locally in a real time graph, using matplotlib. 

Offline:

This includes a number of tools for the purpose of post-analysis of the data. There is another plotting tool using matplotlib, 
an offline gating tool for experimenting with different gate settings and in time more will be added.

Requirements:
  Raspbian, Ubuntu or Windows.
  Python 2.7
  Matplotlib
  PySerial
