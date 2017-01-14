import logging
import time
import threading
from datetime import datetime
import os
from gps import *

from conf import Conf

try:
    import RPi.GPIO as GPIO
except ImportError:
    import fakes.fakegpio as GPIO


"""
    Helper class for bucket actions
"""
class BucketActions:
    STOPPED = 0
    STARTED = 1
    DRIVING = 2

"""
    GPS thread for reading from GPS module
"""
class GpsThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)

        self.m_app = app
        self.m_conf = Conf.Instance()
        self.m_gpsd = gps(mode=WATCH_ENABLE)

        # GPS reading
        self.m_latitude = 0
        self.m_longitude = 0
        self.m_speed = 0
        self.m_altitude = 0
        self.m_date = 0
        self.m_last_refresh = 0
        self.m_bucket_id = self.m_conf.BUCKET_ID
        self.m_bucket_status = BucketActions.STOPPED

        # Reset ports
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(25, GPIO.OUT)  # Reset port for GPS device
        self.gps_reset()
        logging.debug("GPS initialized")

    def _post(self):
        gps_read = self.get_gps()
        logging.info(gps_read)
        if (gps_read['lat'] != 0) or (gps_read['long'] != 0):
            self.m_app.gps_action(gps_read)
        else:
            logging.error("GPS module is not ready yet")

    def _read(self):
        try:
            self.m_gpsd.next()

            time.sleep(0.1)

            # Get the GPS values in object
            self.m_latitude = self.m_gpsd.fix.latitude
            self.m_longitude = self.m_gpsd.fix.longitude
            self.m_date = (datetime.strptime(self.m_gpsd.utc[:19], "%Y-%m-%dT%H:%M:%S")- datetime(1970,1,1)).total_seconds()
            self.m_speed = self.m_gpsd.fix.speed
            self.m_altitude = self.m_gpsd.fix.altitude

            if self.m_speed > 1:
                if self.m_bucket_status == BucketActions.STOPPED:
                    self.m_bucket_status = BucketActions.STARTED
                wait_time = 5  # 5 seconds
            else:
                self.m_bucket_status = BucketActions.STOPPED
                wait_time = 60*10  # 10 minutes

            if self.m_date - self.m_last_refresh >= wait_time or self.m_bucket_status == BucketActions.STARTED:
                if self.m_bucket_status == BucketActions.STARTED:
                    self.m_bucket_status = BucketActions.DRIVING
                self.m_last_refresh = self.m_date
                self._post()

        except Exception as e:
            logging.error("Gps thread exception ignored")
            logging.debug(e)
            time.sleep(0.1)

    def gps_reset(self):
        GPIO.output(25, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(25, GPIO.LOW)
        time.sleep(2)
        GPIO.output(25, GPIO.HIGH)

    def run(self):
        while True:
            self._read()

    def start(self):
        super(GpsThread, self).setDaemon(True)
        super(GpsThread, self).start()

    def get_latitude(self):
        return self.m_latitude

    def get_longitude(self):
        return self.m_longitude

    def get_date(self):
        return self.m_date

    def get_speed(self):
        return self.m_speed

    def get_altitude(self):
        return self.m_altitude

    def get_gps(self):
        return({'lat': self.m_latitude,
                'long': self.m_longitude,
                'date': self.m_date,
                'speed': self.m_speed,
                'alt': self.m_altitude,
                'bucketID': self.m_bucket_id})

if __name__ == '__main__':
    import sys

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    class FakeApp():
        def __init__(self):
            pass

        def gps_action(self, payload):
            logging.info("Gps payload: %s", payload)

    app = FakeApp()

    try:
        gps_reader = GpsThread(app)
        gps_reader.start()
        while True:
            time.sleep(5 * 60)

    except (KeyboardInterrupt, SystemExit):  # When you press ctrl+c
        logging.debug("\nKilling Thread...")
        logging.debug("Done.\nExiting.")
