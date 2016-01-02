#!/usr/bin/env python
import threading

# import base classes and driver
from bibliopixel import LEDStrip

# from bibliopixel.drivers.LPD8806 import DriverLPD8806, ChannelOrder
from bibliopixel.drivers.visualizer import DriverVisualizer, ChannelOrder

# import colors
import bibliopixel.colors

from bibliopixel.animation import BaseStripAnim

from logging import DEBUG, INFO, WARNING, CRITICAL, ERROR
from bibliopixel import log

log.setLogLevel(INFO)


class Worm(BaseStripAnim):
    """
    colors a list the worm segment (starting with head) colors
    path a list of the LED indices over which the worm will travel
    cyclelen controls speed, worm movement only when LED upload
    cycles == 0 mod cyclelen
    height (of worm segments) is same length as colors: higher
    value worms segments go over top of lower value worms
    """
    def __init__(self, led, colors, path, cyclelen, direction=1,
                 height=None, start=0, end=-1):
        super(Worm, self).__init__(led, start, end)
        if height is None:
            height = [0]*len(colors)
        elif type(height) == int:
            height = [height]*len(colors)
        self._colors = colors
        self._colors.append((0, 0, 0))  # add blank seqment to end worm
        self._path = path
        self._cyclelen = cyclelen
        self._height = height
        self._height.append(-1)    # add lowest value for height
        self._activecount = 0
        self._direction = direction
        self._headposition = -self._direction

    def step(self, amt=1):
        if self._activecount == 0:
            self._headposition += amt*self._direction
            self._headposition %= len(self._path)
            # Put worm into strip and blank end
            segpos = self._headposition
            for x in range(len(self._colors)):
                if True:  #self._height[x] >= LEDsegheights[self._path[segpos]]: # or x == len(self.colors) - 1:
                    self._led.set(self._path[segpos], self._colors[x])
                    # LEDsegheights[self._path[segpos]] = self._height[x]
                segpos -= self._direction
                segpos %= len(self._path)
        self._activecount += amt
        self._activecount %= self._cyclelen
        self._step += amt


# load driver and controller and animation queue
# driver = DriverLPD8806(160,c_order = ChannelOrder.GRB, SPISpeed = 16)

# by setting to 160 pixels and size 31 will produce 10 h, 16 wide
#  wrapped
driver = DriverVisualizer(160, pixelSize=31, stayTop=True)

print 'before led instantiation'
print threading.enumerate()

# not much difference whether set threadedUpdate to True or False
#  But CANT stop the updateThread see end of code
led = LEDStrip(driver, threadedUpdate=True)

# led = LEDStrip(driver)
print 'after led instantiation'
print threading.enumerate()

#  Set up worms - my 160 led strip is wound in a spiral around a
#  cylinder approximately  10 times. Led's x+16 is above and only
#  slightly to left of led x. While led x+17 is above and a bit more to right.

# lnin = [255, 255>>1, 255>>2, 255>>3, 255>>4, 255>>5, 255>>6 ]
lnin = [255, 222, 200, 150, 125]
# lnin = lnin * 10
bluedimming = [(0, 0, i) for i in lnin]
reddimming = [(i, 0, 0) for i in lnin]
greendimming = [(0, i, 0) for i in lnin]
cyandimming = [(0, i, i) for i in lnin]
whitedimming = [(i, i, i) for i in lnin]


def pathgen(nleft=0, nright=15, nbot=0, ntop=9, shift=0, turns=10, rounds=16):
    """
    A path around a rectangle from strip wound helically
    10 turns high by 16 round.
    rounds * turns must be number of pixels on strip
    nleft and nright is from 0 to rounds-1, 
    nbot and ntop from 0 to turns-1
    """
    nled = rounds*turns
    adjtop = (turns - ntop - 1)*rounds
    adjbot = nbot*rounds
    ff = nleft+adjtop
    sleft = range(ff, nled-adjbot, rounds)
    tp = range(sleft[-1] + 1, sleft[-1] + nright - nleft)
    sright = range(tp[-1] + 1, 0 + adjtop, -rounds)
    bt = range(sright[-1] - 1, ff, -1)
    path = (sleft+tp+sright+bt)
    path = map(lambda x: (shift+x) % nled, path)
    return path

print 'before animation instantiation'
print threading.enumerate()
#  path = range(11,160,16)+range(12,160,16)[::-1]+range(13,160,16)+range(14,160,16)[::-1]
wormblue = Worm(led, bluedimming, pathgen(0, 15, 0, 9), 1, 1)
wormred = Worm(led, reddimming, pathgen(1, 14, 1, 8), 1, -1)

#wormgreen = Worm(led, greendimming, pathgen(2, 13, 2, 7), 1, 1)
#wormcyan = Worm(led, cyandimming, pathgen(3, 12, 3, 6), 1, -1)

wormgreen = Worm(led, greendimming, pathgen(2, 9, 2, 7), 1, 1)
wormcyan = Worm(led, cyandimming, pathgen(6, 13, 2, 7), 1, -1)

wormwhite = Worm(led, whitedimming, pathgen(4, 11, 4, 5), 1, 1)

print 'after animation instantiation'
print threading.enumerate()

runtime = 10

# wormblue.run(fps=24, max_steps=100, threaded=True)
wormblue.run(fps=24, max_steps=runtime*24, threaded=True)
wormred.run(fps=20, max_steps=runtime*20, threaded=True)
wormgreen.run(fps=16, max_steps=runtime*16, threaded=True)
wormcyan.run(fps=12, max_steps=runtime*12, threaded=True)
wormwhite.run(fps=8, max_steps=runtime*8, threaded=True)

# idle and threaded animations will run jointly
print 'after start animation'
print threading.enumerate()

tt = 0
# oldb = led.buffer[:]

# don't need this wait loop but will leave animation threads running
# but don't try and stop updateThread before they finish
wormlist = [wormblue, wormred, wormgreen, wormcyan, wormwhite]

while not all([w.stopped() for w in wormlist]):
    # while not wormblue.stopped() or not wormred.stopped() or not wormgreen.stopped()   or not wormcyan.stopped():
    tt += 1
    # if led.buffer != oldb:
    #    print filter(lambda x:x!=0,led.buffer)
    #    oldb = led.buffer[:]
    # print led.buffer
    pass

print "Ya Hoo"
print tt

print 'after all animations stopped'
print threading.enumerate()


# Not sure is need or want this
led.waitForUpdate()

# NOTE if stop updateThreads while animations still running
#  havoc!
#  test new routine
led.stopUpdateThreads()


print 'after stopped updateThread'
print threading.enumerate()
