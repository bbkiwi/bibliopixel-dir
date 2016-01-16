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



class Dummy(BaseStripAnim):
    def __init__(self, led, start=0, end=-1):
        super(Dummy, self).__init__(led, start, end)

    def step(self, amt=1):
        pass

if __name__ == '__main__':
    pixelWidth = 10
    masterBrightness = 200
    driver = DriverVisualizer(160, pixelSize=8, stayTop=True)
    led = LEDStrip(driver, pixelWidth=pixelWidth,  masterBrightness=masterBrightness)
    dum = Dummy(led)
      
    print "masterBrightness is {}".format(dum._led.masterBrightness)  
    dum._led.all_off()
    print "Pixel width {}".format(dum._led.pixelWidth) 
    print "Numer of scaled pixels {}".format(dum._led.numLEDs)
    print "set scaled pixel 14 to red and scaled pixel 15 to green"    
    print "these colors are scaled via masterBrightness"    
    dum._led.set(14,(255, 0 ,0))
    dum._led.update()
    px1c = (0, 255 ,0)
    dum._led.set(15, px1c)
    dum._led.update()
    print "But when ask for pixel 14s color get {}".format(dum._led.get(14))
    print "Is it the value we set? {}".format(dum._led.get(14) == (255, 0, 0))
    print "But when ask for pixel 15s color get {}".format(dum._led.get(15))
    print "Is it the value we set? {}".format(dum._led.get(15) == px1c)
    print "use fill to make pixels 3,4,5,6 white"
    dum._led.fill((255,255,255),3,6)
    dum._led.update()
    print "Where they set? {}".format(all([dum._led.get(p) == (255,255,255) for p in range(3,7)]))
 
    
