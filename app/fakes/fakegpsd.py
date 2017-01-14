import logging

'''
    Fake GPS for simulation tests
'''

WATCH_ENABLE = 1

def NMEAStreamReader(mode):
    logging.debug("gps() in mode: %s", mode)
    return gpsd()

class fix():
    def __init__(self):
        self.latitude = 10
        self.longitude = 20
        self.time = 23983
        self.speed = 20
        self.altitude = 40

class gpsd():
    def __init__(self):
        self.fix = fix()
        self.utc = 'May 10 2015'

    def next(self):
        logging.debug("next() called")
