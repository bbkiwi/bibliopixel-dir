#!/usr/bin/env python
"""
Tests: 
Minor bugs related to scaled pixels in Strip and Matrix
and masterBrigthness

setting a given pixel to a given color and then asking for it with get should 
return the same value.
"""


from bibliopixel import LEDStrip, LEDMatrix
from bibliopixel.drivers.visualizer import DriverVisualizer
from bibliopixel.animation import BaseStripAnim, BaseMatrixAnim,  AnimationQueue
from logging import DEBUG, INFO, WARNING, CRITICAL, ERROR
from bibliopixel import log
log.setLogLevel(INFO)
import time
import random


class Dummy(BaseMatrixAnim):
    def __init__(self, led, width=16, height=10, start=0, end=-1):
        super(Dummy, self).__init__(led, start, end)

    def step(self, amt=1):
        pass

if __name__ == '__main__':
    pixelSize = (2,2)
    masterBrightness = 200
    
    width = 8
    height = 8
    driver = DriverVisualizer(width=width, height=height, pixelSize=50, stayTop=True)
    led = LEDMatrix(driver, pixelSize=pixelSize,  masterBrightness=masterBrightness)
    ri = random.randint
    tex = [[(ri(0,255), ri(0,255), ri(0,255)) for i in range(width / pixelSize[0])] 
              for j in range(height / pixelSize[1]) ]
    dum = Dummy(led)
    dum._led.setTexture(tex)
    dum._led.all_off()
    print "masterBrightness is {}".format(dum._led.masterBrightness)
    print "Pixel size {}".format(dum._led.pixelSize) 
    print "Numer of scaled pixels {}".format(dum._led.numLEDs)
    print "set scaled pixel 0,0 to red and scaled pixel 1,0 to green scaled pixel 1,2 to texture"    
    dum._led.set(0, 0,(255, 0 ,0))
    dum._led.update()
    px1c = (0, 255 ,0)
    dum._led.set(1, 0, px1c)
    dum._led.update()
    dum._led.set(1, 2)
    dum._led.update()
    print "get scaled pixel at (1, 0) color returns {}".format(dum._led.get(1, 0))
    print "Are they the same? {}".format(dum._led.get(1, 0) == px1c)
    print "get scaled pixel at (1, 2) color returns {} and texture is {}".format(dum._led.get(1, 2), tex[2][1])
    print "Are they the same? {}".format(dum._led.get(1, 2) == tex[2][1])
