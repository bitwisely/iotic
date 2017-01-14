import logging
import sys
import time
import Queue
import threading
import datetime

from conf import Conf
from monitorthread import MonitorThread
from serverthread import ServerThread
from gpsthread import GpsThread
from rfidreaderthread import RfIDReaderThread
from buzzerthread import BuzzerThread
from tiltthread import TiltThread


"""
    Helper class for app actions
"""
class AppActions:
    UNKNOWN = 0
    TILT_TRIGGER = 1
    GPS_TRIGGER = 2


class AppThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.m_app = self
        self.m_process_queue = Queue.Queue()
        self.m_date = int(datetime.datetime.now().strftime("%s")) * 1000
        self.m_current_tag_id = ""
        self.m_current_picture_id = ""
        self.m_tag_read_retry = 0

        # Generate objects
        self.m_conf = Conf.Instance()
        self.m_monitor = MonitorThread(self.m_app)
        self.m_server = ServerThread()
        self.m_gps_reader = GpsThread(self.m_app)
        self.m_reader = RfIDReaderThread()
        self.m_buzzer = BuzzerThread()

        if self.m_conf.CAMERA_ENABLED:
            from camerathread import CameraThread
            self.m_camera = CameraThread()
        else:
            self.m_camera = None

        self.m_tilt = TiltThread(self.m_app)

        # Start threads
        self.m_server.start()
        self.m_monitor.start()
        self.m_gps_reader.start()
        self.m_reader.start()
        self.m_buzzer.start()

        if self.m_camera:
            self.m_camera.start()

        self.m_tilt.start()

        logging.info("App thread is initialized.")

    # Callback function for completed RFID reads
    def _reader_cb(self, err, tag_id):

        if err:
            self.m_server.post_log_msg(err)

        elif not tag_id:
            if self.m_tag_read_retry < self.m_conf.MAX_TAG_READ_CNT:
                self.m_tag_read_retry += 1
                time.sleep(0.2)
                self.tilt_action()  # Resend a new read request to its own queue
                logging.info("No TAG. Re-read try count: %d", self.m_tag_read_retry)
            else:
                logging.info("No TAG could be found after tilt action")
                self.m_tag_read_retry = 0
        else:
            self.m_tag_read_retry = 0
            temp_str = str(tag_id)
            self.m_current_tag_id = temp_str.strip()
            self.m_current_picture_id = temp_str.strip() + '_' + str(self.m_date)

            data = {'bucketID': self.m_conf.BUCKET_ID,
                    'tagID': self.m_current_tag_id,
                    'lat': self.m_gps_reader.get_latitude(),
                    'long': self.m_gps_reader.get_longitude(),
                    'date': self.m_date,
                    'pictureID': self.m_current_picture_id}
            self.m_server.post_tag_data(data)

            if self.m_camera:
                self.m_camera.take_picture(self._capture_cb)

            self.m_buzzer.beep_ok()

    def _capture_cb(self, err):
        print ("Capture Picture CB called")
        print(err)
        if err:
            logging.error("Could not capture tag picture")
        else:
            data = {'pictureID': self.m_current_picture_id}
            self.m_server.post_tag_picture(data, self.m_conf.CAPTURED_SNAPSHOT)

    def _action_processor(self, msg):
        if msg['action'] == AppActions.TILT_TRIGGER:
            self.m_date = int(datetime.datetime.now().strftime("%s")) * 1000
            self.m_reader.read(self._reader_cb)

        if msg['action'] == AppActions.GPS_TRIGGER:
            self.m_server.post_bucket_data(msg['payload'])

    def run(self):
        while True:
            # Push data to SQLite from SQLite write queue
            msg = self.m_process_queue.get()
            self._action_processor(msg)
            logging.debug(msg)
            self.m_process_queue.task_done()

    def start(self):
        super(AppThread, self).setDaemon(True)
        super(AppThread, self).start()

    # API for actions triggered from other threads
    def tilt_action(self):
        self.m_process_queue.put({'action': AppActions.TILT_TRIGGER,
                                  'payload': None})

    def gps_action(self, payload):
        self.m_process_queue.put({'action': AppActions.GPS_TRIGGER,
                                  'payload': payload})

if __name__ == '__main__':

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    # Log options: debug, info, warning, error and critical
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format=FORMAT)

    try:
        app = AppThread()
        app.start()
        app.m_server.post_log_msg("APP_VER: " + app.m_conf.APP_REL_VERSION + " APP_DATE: " + app.m_conf.APP_REL_DATE)
        t = 0
        while True:
            app.m_server.post_log_msg("APP_IS_RUNNING FOR " + str(int(t/4)) + " HOURS, " + str((t % 4)*15) + " MINUTES")
            time.sleep(60*1*15)  # 15 minutes
            t += 1
   
    except:
        app.m_server.post_log_msg("APP_STOPPED")
        logging.info("APP terminating.")

        if app and app.m_camera:
            app.m_camera.close()

        # TODO: Thread stop never occurs. Need to fix.
        #app.m_sqlite_store.running = False
        #app.m_sqlite_store.join()
        logging.info("APP terminated.")
