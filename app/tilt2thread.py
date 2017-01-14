import logging
import time
import threading

from conf import Conf


try:
    import RPi.GPIO as GPIO
except ImportError:
    import fakes.fakegpio as GPIO

"""
    Helper class for lifter state
"""
class LifterState:
    UNKNOWN = 0
    UP = 1
    GOING_UP = 2
    GOING_DOWN = 3
    DOWN = 4

"""
    Threaded class  which reads tilt sensor state and when lift is going up initiates tag read via app object

    @param app object
"""
class TiltThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)

        self.m_conf = Conf.Instance()
        self.m_app = app

        self.m_sensor_1 = 0
        self.m_sensor_2 = 0
        self.m_read_trigger = False
        self.m_lifter_state = LifterState.UNKNOWN

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(26, GPIO.IN)
        GPIO.setup(19, GPIO.IN)
        logging.debug("Tilt thread initialized")

    def run(self):
        while True:
            self.sensor1_read()
            self.sensor2_read()
            self.lifter_state()     # Update bucket lifter state
            self.execute_capture()  # Take a capture based on bucket lifter state
            time.sleep(0.1)

    def sensor1_read(self):
        self.m_sensor_1 = GPIO.input(26)

    def sensor2_read(self):
        self.m_sensor_2 = GPIO.input(19)

    def lifter_state(self):
        if self.m_sensor_1 == 1 and self.m_sensor_2 == 1:
            if self.m_lifter_state == LifterState.UNKNOWN or self.m_lifter_state == LifterState.DOWN:
                self.m_lifter_state = LifterState.GOING_UP
            elif self.m_lifter_state == LifterState.GOING_UP:
                self.m_lifter_state = LifterState.UP
            #logging.info("Tilt sensor state: %d", self.m_lifter_state)
        elif self.m_sensor_1 == 0 and self.m_sensor_2 == 0:
            if self.m_lifter_state == LifterState.UNKNOWN or self.m_lifter_state == LifterState.UP:
                self.m_lifter_state = LifterState.GOING_DOWN
            elif self.m_lifter_state == LifterState.GOING_DOWN:
                self.m_lifter_state = LifterState.DOWN
            #logging.info("Tilt sensor state: %d", self.m_lifter_state)
        else:
            #logging.error("Tilt sensor inconsistent measurement detected!")
            pass

    def execute_capture(self):
        if self.m_lifter_state == LifterState.GOING_UP:
            logging.info("Tilt action message send to app.")
            self.m_app.tilt_action()

if __name__ == '__main__':
    import sys

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    class FakeApp():
        def __init__(self):
            pass

        def tilt_action(self):
            logging.debug("Fake app received a tilt action")

    app = FakeApp()

    try:
        t = TiltThread(app)
        t.start()
        while True:
            time.sleep(10)

    except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
        logging.debug("\nKilling Thread...")
        t.running = False
        t.join() # wait for the thread to finish what it's doing
        logging.debug("Done.\nExiting.")