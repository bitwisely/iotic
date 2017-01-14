import logging
import time
import Queue
import threading
import pyscreenshot

'''
    Fake Camera for simulation tests
'''

class PiCamera(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.m_process_queue = Queue.Queue()
        self.resolution = ()

    def stop_preview(self):
        logging.debug("Stop camera")

    def start(self):
        logging.debug("Start camera")

    def close(self):
        logging.debug("Close camera")

    def capture(self, path):
        logging.debug("Capture to %s", path)
        pyscreenshot.grab_to_file(path)

