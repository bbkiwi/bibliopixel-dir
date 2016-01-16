# -*- coding: utf-8 -*-
"""
Created on Sat Jan 02 17:01:40 2016
Worm animation class
pathgen a helper function for generating rectangular paths in matrix array
@author: Bill
"""
from bibliopixel.animation import BaseStripAnim
from bibliopixel import log

class Worm(BaseStripAnim):
    """
    colors a list the worm segment (starting with head) colors
    path a list of the LED indices over which the worm will travel
    cyclelen controls speed, worm movement only when LED upload
    cycles == 0 mod cyclelen
    height (of worm segments) is same length as colors: higher
    value worms segments go over top of lower value worms  
    Default is for worm on full strip
    Note the worms state is not a direct function of self._step, but
    rather self._headpostion which is initialized. So subsequent worm.run()
    will start where a previous call to worm.run() finished. 
    """
    def __init__(self, led, colors, path=None, cyclelen=1, direction=1,
                 height=None, start=0, end=-1):
        super(Worm, self).__init__(led, start, end)
        if path is None:
            path = range(led.numLEDs)
        self._path = path        
        if height is None:
            height = [0]*len(colors)
        elif type(height) == int:
            height = [height]*len(colors)
        self._colors = colors[:] # protect argument from change
        self._colors.append((0, 0, 0))  # add blank seqment to end worm
        self._cyclelen = cyclelen
        self._height = height[:] # protect argument from change
        self._height.append(-1)    # add lowest value for height
        self._activecount = 0
        self._direction = direction
        self._headposition = -self._direction
        #print self._colors
        #print self._height

    def step(self, amt=1):
        if self._activecount == 0:
            self._headposition += amt*self._direction
            self._headposition %= len(self._path)
            # Put worm into strip and blank end
            segpos = self._headposition
            for x in range(len(self._colors)):
                if True:
                    self._led.set(self._path[segpos], self._colors[x])
                    try:
                        self._led.pixheights[self._path[segpos]] = self._height[x]
                    except AttributeError:
                        pass # if _led can't deal with pixheights
                segpos -= self._direction
                segpos %= len(self._path)
        self._activecount += amt
        self._activecount %= self._cyclelen
        self._step += amt

def pathgen(nleft=0, nright=15, nbot=0, ntop=9, shift=0, turns=10, rounds=16):
    """
    A path around a rectangle from strip wound helically
    10 turns high by 16 round.
    rounds * turns must be number of pixels on strip
    nleft and nright is from 0 to rounds-1, 
    nbot and ntop from 0 to turns-1
    """
    def ind(x, y):
        return x + y * rounds
        
    assert 0 <= nleft <= nright -1 <= rounds and 0 <= nbot <= ntop -1 <= turns
    
    nled = rounds*turns
    sleft = range(ind(nleft, nbot), ind(nleft, ntop), rounds)
    tp = range(ind(nleft, ntop), ind(nright, ntop), 1)
    sright = range(ind(nright, ntop), ind(nright, nbot), -rounds)
    bt = range(ind(nright, nbot), ind(nleft, nbot), -1)
    path = sleft+tp+sright+bt
    if len(path) == 0:
        path = [ind(nleft, nbot)]
    path = map(lambda x: (shift+x) % nled, path)
    log.logger.info("pathgen({}, {}, {}, {}, {}) is {}".format(nleft, nright, nbot, ntop, shift, path))
    return path 
