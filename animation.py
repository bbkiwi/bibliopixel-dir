import time
import log

from led import LEDMatrix
from led import LEDStrip
from led import LEDCircle
import colors

from util import d

import math
import threading


class animThread(threading.Thread):
    def __init__(self, anim, args):
        super(animThread, self).__init__()
        self.setDaemon(True)
        self._anim = anim
        self._args = args

    def run(self):
        log.logger.info("Starting thread...")
        self._anim._run(**self._args)
        log.logger.info("Thread Complete")


class BaseAnimation(object):
    def __init__(self, led):
        self._led = led
        self.animComplete = False
        self._step = 0
        self._timeRef = 0
        self._internalDelay = None
        self._threaded = False
        self._thread = None
        self._callback = None
        self._stopEvent = threading.Event()
        self._stopEvent.clear()

    def _msTime(self):
        return time.time() * 1000.0

    def preRun(self, amt=1):
        self._led.all_off()

    def postRun(self):
        self._led.resetMasterBrightness()

    def preStep(self, amt=1):
        pass

    def postStep(self, amt=1):
        pass

    def step(self, amt=1):
        raise RuntimeError("Base class step() called. This shouldn't happen")

    def stopThread(self, wait=False):
        if self._thread:
            self._stopEvent.set()
            if wait:
                self._thread.join()

    def __enter__(self):
        return self

    def _exit(self, type, value, traceback):
        pass

    def __exit__(self, type, value, traceback):
        self._exit(type, value, traceback)
        self.stopThread(wait=True)
        self._led.all_off()
        self._led.update()
        self._led.waitForUpdate()

    def cleanup(self):
        return self.__exit__(None, None, None)

    def stopped(self):
        if self._thread:
            return not self._thread.isAlive()
        else:
            return True

    def _run(self, amt, fps, sleep, max_steps, untilComplete, max_cycles, updateWithPush=True):
        self.preRun()
        # calculate sleep time (ms) based on desired Frames per Second
        if fps is not None:
            sleep = 1000.0 / fps

        initSleep = sleep

        self._step = 0
        cur_step = 0
        cycle_count = 0
        self.animComplete = False
        
        startupdate = self._msTime() # just to get started
        while not self._stopEvent.isSet() and (
                 (max_steps == 0 and not untilComplete) or
                 (max_steps > 0 and cur_step < max_steps) or
                 (max_steps == 0 and untilComplete and not self.animComplete)):

            self._timeRef = self._msTime()

            start = self._msTime()
            if hasattr(self, "_input_dev"):
                self._keys = self._input_dev.getKeys()
            self.preStep(amt)
            self.step(amt)
            self.postStep(amt)
            mid = self._msTime()

            if self._internalDelay:
                sleep = self._internalDelay
            elif initSleep:
                sleep = initSleep

            self._led._frameGenTime = int(mid - start)
            self._led._frameTotalTime = sleep
            
            # sleep here so update starts on  integer multiple of sleep time
            #   since the time counter began
            #   this will help synchronize concurrent animations
            if sleep:
                # log.logger.warning("min - startupdate %dms  but sleep =  %dms!" % (mid - startupdate, sleep))
                if mid - startupdate < sleep: # startupdate previous iteration
                    tsleep = sleep - (mid - startupdate)
                    # apply correction to end on integer multiple
                    nextstartupdate = startupdate + sleep
                    framesTimeBegan = nextstartupdate / sleep
                    framecorrection = round(framesTimeBegan) - framesTimeBegan
                    tsleep = tsleep + framecorrection * sleep
                    log.logger.info("time correction used %f ms   " % (framecorrection * sleep))
                    # subtle correction to compensate for time of above calc
                    endcalc = self._msTime()
                    if (endcalc - mid) < tsleep:
                        if self._threaded:
                            self._stopEvent.wait(tsleep / 1000.0)
                        else:
                            time.sleep(tsleep / 1000.0)        
#                    # might be able to skip corrections and use this directly                     
#                    if self._threaded:
#                        self._stopEvent.wait(tsleep / 1000.0)
#                    else:
#                        time.sleep(tsleep / 1000.0)        
#                
                else:
                    diff = (self._msTime() - self._timeRef)
                    log.logger.warning("Frame-time of %dms set, but took %dms!" % (sleep, diff))
                          
            startupdate = self._msTime()

            if updateWithPush:
                self._led.update()
            else:
                self._led._updatenow.set()   # signals masterAnimation to act
                
            now = self._msTime()

            if self.animComplete and max_cycles > 0:
                if cycle_count < max_cycles - 1:
                    cycle_count += 1
                    self.animComplete = False

            stepTime = int(mid - start)
            if self._led._threadedUpdate:
                updateTime = int(self._led.lastThreadedUpdate())
                totalTime = updateTime
            else:
                updateTime = int(now - startupdate)
                totalTime = stepTime + updateTime

            if self._led._threadedUpdate:
                log.logger.debug("Id {} Frame: {}ms / Update Max: {}ms".format(id(self), stepTime, updateTime))
            else:
                log.logger.debug("{}ms/{}fps / Frame: {}ms / Update: {}ms".format(totalTime, int(1000 / max(totalTime,1)), stepTime, updateTime))

            cur_step += 1

        self.animComplete = True
        self.postRun()

        if self._callback:
            self._callback(self)

    def run(self, amt = 1, fps=None, sleep=None, max_steps = 0, untilComplete = False, max_cycles = 0, threaded = False, joinThread = False, callback=None, updateWithPush=True):

        self._threaded = threaded
        if self._threaded:
            self._stopEvent.clear()
        self._callback = callback

        if self._threaded:
            args = {}
            l = locals()
            run_params = ["amt", "fps", "sleep", "max_steps", "untilComplete", "max_cycles", "updateWithPush"]
            for p in run_params:
                if p in l:
                    args[p] = l[p]
            self._thread = animThread(self, args)
            self._thread.start()
            if joinThread:
                self._thread.join()
        else:
            self._run(amt, fps, sleep, max_steps, untilComplete, max_cycles, updateWithPush)

    RUN_PARAMS = [{
                "id": "amt",
                "label": "Step Amount",
                "type": "int",
                "min": 1,
                "default": 1,
                "help":"Amount to step animation by on each frame. May not be used on some animations."
            },{
                "id": "fps",
                "label": "Framerate",
                "type": "int",
                "default": 30,
                "min": 1,
                "help":"Framerate at which to run animation."
            },{
                "id": "max_steps",
                "label": "Max Frames",
                "type": "int",
                "min": 0,
                "default": 0,
                "help":"Total frames to run before stopping."
            },{
                "id": "untilComplete",
                "label": "Until Complete",
                "type": "bool",
                "default": False,
                "help":"Run until animation marks itself as complete. If supported."
            },{
                "id": "max_cycles",
                "label": "Max Cycles",
                "type": "int",
                "min": 1,
                "default": 1,
                "help":"If Until Complete is set, animation will repeat this many times."
            },]

class OffAnim(BaseAnimation):
    def __init__(self, led, timeout=10):
        super(OffAnim, self).__init__(led)
        self._internalDelay = timeout * 1000

    def step(self, amt=1):
        self._led.all_off()

class AnimationQueue(BaseAnimation):
    def __init__(self, led, anims=None):
        super(AnimationQueue, self).__init__(led)
        if anims == None:
            anims = []
        self.anims = anims
        self.curAnim = None
        self.animIndex = 0;
        self._internalDelay = 0 #never wait
        self.fps = None
        self.untilComplete = False

    #overriding to handle all the animations
    def stopThread(self, wait = False):
        for a,r in self.anims:
            #a bit of a hack. they aren't threaded, but stops them anyway
            a._stopEvent.set()
        super(AnimationQueue, self).stopThread(wait)

    def addAnim(self, anim, amt = 1, fps=None, max_steps = 0, untilComplete = False, max_cycles = 0):
        a = (
            anim,
            {
                "amt": amt,
                "fps": fps,
                "max_steps": max_steps,
                "untilComplete": untilComplete,
                "max_cycles": max_cycles
            }
        )
        self.anims.append(a)

    def preRun(self, amt=1):
        if len(self.anims) == 0:
            raise Exception("Must provide at least one animation.")
        self.animIndex = -1

    def run(self, amt = 1, fps=None, sleep=None, max_steps = 0, untilComplete = False, max_cycles = 0, threaded = False, joinThread = False, callback=None):
        self.fps = fps
        self.untilComplete = untilComplete
        self.max_cycles = max_cycles
        super(AnimationQueue, self).run(amt = 1, fps=None, sleep=None, max_steps = 0, untilComplete = untilComplete, max_cycles = max_cycles, threaded = threaded, joinThread = joinThread, callback=callback)

    def step(self, amt=1):
        self.animIndex += 1
        if self.animIndex >= len(self.anims):
            if self.untilComplete and self.max_cycles <= 1:
                self.animComplete = True
            else:
                self.max_cycles -= 1
                self.animIndex = 0

        if not self.animComplete:
            self.curAnim = self.anims[self.animIndex]

            anim, run = self.curAnim
            run['threaded'] = False
            run['joinThread'] = False
            run['callback'] = None

            if run['fps'] == None and self.fps != None:
                run['fps'] = self.fps
            anim.run(**(run))

    RUN_PARAMS = [{
                "id": "fps",
                "label": "Default Framerate",
                "type": "int",
                "default": None,
                "min": 1,
                "help":"Default framerate to run all animations in queue."
            },{
                "id": "untilComplete",
                "label": "Until Complete",
                "type": "bool",
                "default": False,
                "help":"Run until animation marks itself as complete. If supported."
            }]

class BaseStripAnim(BaseAnimation):
    def __init__(self, led, start = 0, end = -1):
        super(BaseStripAnim, self).__init__(led)

        if not isinstance(led, LEDStrip):
            raise RuntimeError("Must use LEDStrip with Strip Animations!")

        self._start = start
        self._end = end
        if self._start < 0:
            self._start = 0
        if self._end < 0 or self._end > self._led.lastIndex:
            self._end = self._led.lastIndex

        self._size = self._end - self._start + 1

class BaseMatrixAnim(BaseAnimation):
    def __init__(self, led, width=0, height=0, startX=0, startY=0):
        super(BaseMatrixAnim, self).__init__(led)
        if not isinstance(led, LEDMatrix):
            raise RuntimeError("Must use LEDMatrix with Matrix Animations!")

        if width == 0:
            self.width = led.width
        else:
            self.width = width

        if height == 0:
            self.height = led.height
        else:
            self.height = height

        self.startX = startX
        self.startY = startY

class BaseGameAnim(BaseMatrixAnim):
    def __init__(self, led, inputDev):
        super(BaseGameAnim, self).__init__(led)
        self._input_dev = inputDev
        self._keys = None
        self._lastKeys = None
        self._speedStep = 0
        self._speeds = {}
        self._keyfuncs = {}

    def _exit(self, type, value, traceback):
        if hasattr(self._input_dev, "setLights") and hasattr(self._input_dev, "setLightsOff"):
            self._input_dev.setLightsOff(5)
        self._input_dev.close()

    def setSpeed(self, name, speed):
        self._speeds[name] = speed

    def getSpeed(self, name):
        if name in self._speeds:
            return self._speeds[name]
        else:
            return None

    def _checkSpeed(self, speed):
        return self._speedStep % speed == 0

    def checkSpeed(self, name):
        return (name in self._speeds) and (self._checkSpeed(self._speeds[name]))

    def addKeyFunc(self, key, func, speed = 1, hold = True):
        if not isinstance(key, list):
            key = [key]
        for k in key:
            self._keyfuncs[k] = d({
                "func": func,
                "speed": speed,
                "hold": hold,
                "last": False,
                "inter": False
                })

    def handleKeys(self):
        kf = self._keyfuncs
        for key in self._keys:
            val = self._keys[key]
            if key in kf:
                cfg = kf[key]
                speedPass = self._checkSpeed(cfg.speed)

                if cfg.hold:
                    if speedPass:
                        if (val or cfg.inter):
                            cfg.func()
                        else:
                            cfg.inter = cfg.last = val
                else:
                    if speedPass:
                        if (val or cfg.inter) and not cfg.last:
                                cfg.func()
                        cfg.inter = cfg.last = val
                    else:
                        cfg.inter |= val
        self._lastKeys = self._keys

    def preStep(self, amt):
        pass

    def postStep(self, amt):
        self._speedStep += 1

class BaseCircleAnim(BaseAnimation):
    def __init__(self, led):
        super(BaseCircleAnim, self).__init__(led)

        if not isinstance(led, LEDCircle):
            raise RuntimeError("Must use LEDCircle with Circle Animations!")

        self.rings = led.rings
        self.ringCount = led.ringCount
        self.lastRing = led.lastRing
        self.ringSteps = led.ringSteps

class StripChannelTest(BaseStripAnim):
    def __init__(self, led):
        super(StripChannelTest, self).__init__(led)
        self._internalDelay = 500
        self.colors =  [colors.Red, colors.Green, colors.Blue, colors.White]

    def step(self, amt = 1):

        self._led.set(0, colors.Red)
        self._led.set(1, colors.Green)
        self._led.set(2, colors.Green)
        self._led.set(3, colors.Blue)
        self._led.set(4, colors.Blue)
        self._led.set(5, colors.Blue)

        color =  self._step % 4
        self._led.fill(self.colors[color], 7, 9)

        self._step += 1

class MatrixChannelTest(BaseMatrixAnim):
    def __init__(self, led):
        super(MatrixChannelTest, self).__init__(led, 0, 0)
        self._internalDelay = 500
        self.colors =  [colors.Red, colors.Green, colors.Blue, colors.White]

    def step(self, amt = 1):

        self._led.drawLine(0, 0, 0, self.height - 1, colors.Red)
        self._led.drawLine(1, 0, 1, self.height - 1, colors.Green)
        self._led.drawLine(2, 0, 2, self.height - 1, colors.Green)
        self._led.drawLine(3, 0, 3, self.height - 1, colors.Blue)
        self._led.drawLine(4, 0, 4, self.height - 1, colors.Blue)
        self._led.drawLine(5, 0, 5, self.height - 1, colors.Blue)

        color =  self._step % 4
        self._led.fillRect(7, 0, 3, self.height, self.colors[color])

        self._step += 1

class MatrixCalibrationTest(BaseMatrixAnim):
    def __init__(self, led):
        super(MatrixCalibrationTest, self).__init__(led, 0, 0)
        self._internalDelay = 500
        self.colors = [colors.Red, colors.Green, colors.Green, colors.Blue, colors.Blue, colors.Blue]

    def step(self, amt = 1):
        self._led.all_off()
        i = self._step % self.width
        for x in range(i + 1):
            c = self.colors[x % len(self.colors)]
            self._led.drawLine(x, 0, x, i, c)

        self.animComplete = (i == (self.width-1))

        self._step += 1

class MasterAnimation(BaseMatrixAnim):
    """
    NOTE this version requires a modified BaseAnimation class
    ma = MasterAnimation(ledmaster, animTracks, runtime=1)
    Runs a number of animation tracks concurrently. 
    animTracks is list of tuples
          (animation with unique led, pixmap, pixheights, fps)
    All the animations in animTracks will run for runtime. Each of the
    animations, a, is mapped into ledmaster by its pixmap and conflicts 
    resolved by pixheights.
    For each tuple in animTracks consists of:
       animation e.g. a = Wave(LEDStrip(Driver...(num ..), ...)
           All of the animations in animTracks must have distinct instances
               of LEDStrip, LEDMatrix, ...!
           TODO fix this!
           Any Driver should be ok. Specifying threaded=False is recommended
              but it probably makes no difference. The updating is very
              fast as it is only signally MasterAnimation to act. 
       pixmap is list of size a._led.numLEDs of pixel indices of ledmaster
         if pixmap is None, it will be replaced by range(a._led.numLEDs)
       pixheights is list of size a._led.numLEDs of floats. Highest pixels
         are the ones that display. In case of ties, xor is used
         if pixheights is one value, pixheights is replaced by 
         the constant list. If pixheights is None the constant is 0
       fps a int or None for frames per second for this animation
          
    ma.run(fps=None, threaded=False) will run all the animiation tracks
       concurrently and wait till the runtime is over.       
    if fps is set faster frames from the tracks will be skipped. 
   
    if threaded is True is will not wait. 
    To wait use:
    while not masteranimation.stopped():
        pass
    """
    def __init__(self, led, animTracks, runtime=10, start=0, end=-1):
        super(MasterAnimation, self).__init__(led, start, end)
        
        # Early idea but don't like breaking _led 
        # XXX a replacement update function for animations in animTracks
        # XXXdef __update(self):
        # XXX   self._updatenow.set() 
           
        if not isinstance(animTracks, list):
            animTracks = [animTracks]
        self._animTracks = animTracks
        # modify the update methods of led and add threading Event atribute
        self._ledcopies = []
        #XXX self._restoreupdates = []
        
        # for all animations' leds add attributes: _updatenow, pixmap, pixheights
        ledcheck = set()
        self.ledsunique = True
        for a, pixmap, pixheights, f in self._animTracks:
            # check that all the a have distinct ._led
            # TODO make distince copies (deepcopy didn't work, if I could just find the
            #   the defining arguments could make new instance)
            if id(a._led) in ledcheck:
                self.ledsunique = False
                # TODO might only want a warning
                raise RuntimeError('LEDs are not unique for the concurrent animations')
            else:
                ledcheck.add(id(a._led))
                
            a._led._updatenow = threading.Event()
            
            #XXXself._restoreupdates.append(a._led.update)
            #XXXa._led.update = new.instancemethod(__update, a._led, None)
            
            if pixmap is None and not hasattr(a._led, 'pixmap'):
                a._led.pixmap = range(a._led.numLEDs)
            elif pixmap is not None:
                a._led.pixmap = pixmap  
                
            try:          
                if len(a._led.pixmap) != a._led.numLEDs:
                    raise TypeError()                  
            except TypeError:
                err = 'pixmap must be list same size as LEDs'
                log.logger.error(err)
                raise TypeError
                       
            if pixheights is None and not hasattr(a._led, 'pixheights'):
                a._led.pixheights = None
            elif pixheights is not None:
                a._led.pixheights = pixheights 
                
            err = 'pixheights must be list of values same size as LEDs'        
            if a._led.pixheights == None:
                a._led.pixheights = [0] * a._led.numLEDs
            elif isinstance(a._led.pixheights ,list):
                try:
                    if len(a._led.pixheights) != a._led.numLEDs:
                        raise TypeError()                  
                except TypeError:
                    log.logger.error(err)
                    raise TypeError
            else:
                try:
                    a._led.pixheights = [float(a._led.pixheights)] * a._led.numLEDs
                except ValueError:
                    err = 'pixheights must be list of values same size as LEDs'
                    log.logger.error(err)
                    raise ValueError            
                
            self._ledcopies.append(a._led)
            
        self._runtime = runtime
        self._idlelist = []
        self.timedata = [[] for _  in self._animTracks] # [[]] * k NOT define k different lists!
        self._led.pixheights = [0] * self._led.numLEDs
        

    #overriding to handle all the animations
    def stopThread(self, wait = False):
        for w, pm, ph, f in self._animTracks:
            w._stopEvent.set()
        super(MasterAnimation, self).stopThread(wait)


    def preRun(self, amt=1):
        super(MasterAnimation, self).preRun(amt)
        self.starttime = time.time()
        for w, pm, ph, f in self._animTracks:
            w.run(fps=f, max_steps=self._runtime * f, threaded = True, updateWithPush=False)
        #print "In preRUN THREADS: " + ",".join([re.sub('<class |,|bibliopixel.\w*.|>', '', str(s.__class__)) for s in threading.enumerate()])

    def preStep(self, amt=1):
        # only step the master thread when something from ledcopies
        self._idlelist = [True] # to insure goes thru while loop at least once
        while all(self._idlelist):
            self._idlelist = [not ledcopy._updatenow.isSet() for ledcopy in self._ledcopies]
            if self._stopEvent.isSet() | all([a.stopped() for a, pm, ph, f in self._animTracks]):
                self.animComplete = True
                #print all([a.stopped() for a, f in self._animTracks])
                #print 'breaking out'
                break
        self.activeanimind = [i for i, x in enumerate(self._idlelist) if x == False]
        # keep list of pixels changed by the active animations
        self.activepixels = set()
        for i in self.activeanimind:
            self.activepixels = self.activepixels.union(set(self._ledcopies[i].pixmap))
#
    def postStep(self, amt=1):
        # clear the ones found in preStep
        [self._ledcopies[i]._updatenow.clear() for i in self.activeanimind]
        #self.animComplete = all([a.stopped() for a, f in self._animTracks])
        #print "In postStep animComplete {}".format(self.animComplete)

    def step(self, amt=1):
        """
        combines the buffers from the slave led's
        which then gets sent to led via update
        """
        def xortuple(a, b):
            return tuple(a[i] ^ b[i] for i in range(len(a)))
        # For checking if all the animations have their frames looked at
        #print "Anim {} at {:5g}".format(self.activeanimind, 1000*(time.time() - starttime))
 
       # save times activated for each animation
        [self.timedata[i].append(1000*(time.time() - self.starttime)) for i, x in enumerate(self._idlelist) if x == False]

        self._led.pixheights = [-10000] * self._led.numLEDs
        for ledcopy in self._ledcopies:
            # deals with all the pixels from each animation
            #for pixind, pix in enumerate(ledcopy.pixmap):
            # only deal with pixels that got changed
            active = ((pixind, pix) for pixind, pix in enumerate(ledcopy.pixmap) if pix in self.activepixels)
            for pixind, pix in active:
                if self._led.pixheights[pix] == ledcopy.pixheights[pixind]:
                    self._led._set_base(pix,
                            xortuple(self._led._get_base(pix), ledcopy._get_push(pixind)))
                elif self._led.pixheights[pix] < ledcopy.pixheights[pixind]:
                    self._led._set_base(pix, ledcopy._get_push(pixind))
                    self._led.pixheights[pix] = ledcopy.pixheights[pixind]
        self._step += 1


    def run(self, amt = 1, fps=None, sleep=None, max_steps = 0, untilComplete = True, max_cycles = 0, threaded = True, joinThread = False, callback=None):
        super(MasterAnimation, self).run(amt = 1, fps=fps, sleep=None, max_steps = max_steps, untilComplete = untilComplete, max_cycles = 0, threaded = threaded, joinThread = joinThread, callback=callback)
#        while not self.animComplete:
#            pass


