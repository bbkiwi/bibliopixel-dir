from driver_base import *
import time
import threading

import bibliopixel.log as log

class DriverSlave(DriverBase):
    """For use with concurrent threaded animations"""
    
    def __init__(self, num, pixmap=None, pixheights=None):
        """
        num is number of pixels
        pixmap is list of size num with values in range of pixels in master LED
          if None specified becomes range(num)
        pixheights is list of size num with heights
          if None specified becomes all zeros
          if one value specified becomes all that value
        """
        super(DriverSlave, self).__init__(1) # the driver base doesn't need a big buffer
        self.numLEDs = num
        
        if pixmap == None:
            self.pixmap = range(num)
        else:
            try:
                self.pixmap = pixmap
                if len(pixmap) != self.numLEDs:
                    raise TypeError()                  
            except TypeError:
                err = 'pixmap must be list same size as LEDs'
                log.logger.error(err)
                raise TypeError
        
        err = 'pixheights must be list of values same size as LEDs'        
        if pixheights == None:
            self.pixheights = [0] * self.numLEDs
        elif isinstance(pixheights ,list):
            try:
                self.pixheights = pixheights
                if len(pixheights) != self.numLEDs:
                    raise TypeError()                  
            except TypeError:
                log.logger.error(err)
                raise TypeError
        else:
            try:
                self.pixheights = [float(pixheights)] * self.numLEDs
            except ValueError:
                err = 'pixheights must be list of values same size as LEDs'
                log.logger.error(err)
                raise ValueError
              
        self._updatenow = threading.Event()

    #Push new data to strand
    def update(self, data):
        if self._thread == None:
            self._updatenow.set()   
        else:
            raise NameError('slave drivers should be run as NOT threaded')
            quit()
           
