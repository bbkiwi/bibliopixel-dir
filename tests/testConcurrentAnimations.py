#!/usr/bin/env python
"""
Use version of MasterAnimation that adds pixmap and pixheights attributes
  to the led associated with the animations run concurrently
  Runs a number of wave animations on 'strips' embedded in a matrix
"""
# import base classes and driver
from bibliopixel import LEDStrip, LEDMatrix
from bibliopixel.drivers.LPD8806 import DriverLPD8806, ChannelOrder
from bibliopixel.drivers.visualizer import DriverVisualizer, ChannelOrder
from bibliopixel.drivers.dummy_driver import DriverDummy
# import colors
import bibliopixel.colors 
from bibliopixel.animation import BaseStripAnim, BaseMatrixAnim, MasterAnimation
from logging import DEBUG, INFO, WARNING, CRITICAL, ERROR
from bibliopixel import log
log.setLogLevel(WARNING)
import re
import time
from operator import or_, ior, ixor
# import matplotlib.pyplot as plt
import BiblioPixelAnimations.matrix.bloom as BA
import BiblioPixelAnimations.strip.Wave as WA
import sys

from bibliopixel.tests.wormanimclass import pathgen
# set up led with it's driver for the MasterAnimation
try: # to use visualizer but if fails
    drivermaster = DriverVisualizer(160, pixelSize=62, stayTop=False, maxWindowWidth=1024)
    ledmaster = LEDMatrix(drivermaster, width=16, height=10, threadedUpdate=False)
except:
    # assume on my pi and connect to strip, however a process of visualizerUI.py will have
    # been started and will fail
    drivermaster = DriverLPD8806(160)
    ledmaster = LEDMatrix(drivermaster, width=16, height=10, threadedUpdate=False)


# Set up animations that will run concurrently
# Wave arguments
waveblue = ((0,0,255), 1)
wavered = ((0, 255, 0), 1)
wavegreen = ((255, 0, 0), 1)
wavecyan = ((255, 0, 255), 1)
wavewhite = ((255, 255, 255), 1)

# Wave slave driver arguments
wavebluepixmap = pathgen(1, 15, 0, 9)
waveredpixmap = pathgen(1, 14, 1, 8)
wavegreenpixmap = pathgen(2, 13, 2, 7)
wavecyanpixmap = pathgen(3, 12, 3, 6)
wavewhitepixmap = pathgen(4, 11, 4, 5)

# List of triple (animation arguments, slavedriver argument, fps)
wavedatalist = [(waveblue, wavebluepixmap, 5),
                (wavered, waveredpixmap, 6),
                (wavegreen, wavegreenpixmap, 7),
                (wavecyan, wavecyanpixmap, 8),
                (wavewhite, wavewhitepixmap, 9)]

# Each animation must have their own leds
# ledlist is list of unique leds
#   note DriverDummy is used here but any driver can be used as it is ignored
ledlist = [LEDStrip(DriverDummy(len(sarg)), threadedUpdate=False, 
                    masterBrightness=255) for aarg, sarg, fps in wavedatalist]

# Make the animation list
# Worm animations as list tuple (animation instances, pixmap, pixheights, fps) added
animationlist = [(WA.WaveMove(ledlist[i], *wd[0]), wd[1], -1, wd[2]) 
                    for i, wd in enumerate(wavedatalist)]

# needed to run on pixelweb     
def genParams():
    return {"start":0, "end":-1, "animTracks": animationlist}

if __name__ == '__main__':  
    masteranimation = MasterAnimation(ledmaster, animationlist, runtime=2)

    # Master launches all in animationlist at preRun
    # Master steps when it gets a go ahdead signal from one of the
    # concurrent annimations
    masteranimation.run(fps=None, threaded = False)  # if give fps for master will skip faster frames 
    masteranimation.stopThread() 
    
    #import threading
    #print threading.enumerate()
    
    # plot timing data collected from all the animations
    # horizontal axis is time in ms
    # vertical are the various animation and dot is when update sent to leds by master
    try: 
        import matplotlib.pyplot as plt
        plt.clf()
        col = 'brgcwk'
        [plt.plot(masteranimation.timedata[i], [i] * len(masteranimation.timedata[i]), col[i%6]+'o') for i in range(len(animationlist))]
        ax = plt.axis()
        delx = .01 * (ax[1] - ax[0])
        plt.axis([ax[0]-delx, ax[1]+delx, ax[2]-1, ax[3]+1]) 
        plt.title("Master Animation Step Count {}".format(masteranimation._step))
    except ImportError:
        print 'Wasnt able to plot as matplotlib not available'
        pass
    
MANIFEST = [
    {
        "class": MasterAnimation, 
        "type": "preset",
        "preset_type": "animation",
        "controller": "matrix", 
        "desc": None, 
        "display": "Waves in Rings", 
        "id": "MMasterAnimation4", 
        "params": [
            {
                "default": 10, 
                "help": "", 
                "id": "runtime", 
                "label": "Runtime", 
                "type": "int"
            }
        ], 
        "preconfig": genParams, 
    }
]


 