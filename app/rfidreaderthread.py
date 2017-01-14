import logging
import Queue
import threading
import subprocess

from conf import Conf


try:
    import RPi.GPIO as GPIO
except ImportError:
    import fakes.fakegpio as GPIO

"""
    Threaded class  which reads tags from RFID reader and call the callback function passed to it process queue with
    the found tag ID's. If read fails send error message to server.

    @param Server object
"""
class RfIDReaderThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        self.m_process_queue = Queue.Queue()
        self.m_conf = Conf.Instance()

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(18, GPIO.OUT) # Reset port
        GPIO.output(18, GPIO.HIGH)

    def reset(self):
        GPIO.output(18, GPIO.LOW)
        time.sleep(2)
        GPIO.output(18, GPIO.HIGH)

    def _exathing_read(self):
        return subprocess.check_output([self.m_conf.RFID_APP, self.m_conf.RFID_DEVICE])

    def _execute_from_queue(self):
            cb_fn = self.m_process_queue.get()
            try:
                result = self._exathing_read()
                cb_fn(False, result)

            except Exception as e:
                logging.error("Exception")
                logging.error(e)
                cb_fn(True, e)

            self.m_process_queue.task_done()

    def run(self):
        while True:
            self._execute_from_queue()

    def start(self):
        super(RfIDReaderThread, self).setDaemon(True)
        super(RfIDReaderThread, self).start()

    def read(self, cb):
        self.m_process_queue.put(cb)


if __name__ == '__main__':
    import sys
    import time

    from serverthread import ServerThread

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    def rfid_read_cb(err, msg):
        logging.info(msg)

    try:
        server = ServerThread()
        server.start()

        t = RfIDReaderThread()
        t.start()

        while True:
            t.read(rfid_read_cb)
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        logging.debug("\nKilling Thread...")
        t.running = False
        t.m_process_queue.join() # wait for the queue to finish what it's doing
        t.join() # wait for the thread to finish what it's doing
        logging.debug("Done.\nExiting.")
