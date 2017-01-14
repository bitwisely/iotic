import logging

'''
    Fake GPIO for simulation tests
'''

BCM = "bcm"
OUT = "out"
IN = "in"
HIGH = "high"
LOW = "low"

def setwarnings(state):
    logging.debug("state: %s", state)

def setmode(mode):
    logging.debug("mode: %s", mode)

def setup(port, conf):
    logging.debug("port: %s, conf: %s", port, conf)

def output(port, conf):
    logging.debug("port: %s, conf: %s", port, conf)

def input(port):
    logging.debug("port: %s", port)