import logging

from helpers.singleton import Singleton
from helpers.rpserial import RpSerial
from diskmount import DiskMount

from ntpd import Ntpd


# Set this to "mac" for local tests, set "aws" for AWS tests.
g_test_mode = "aws"

"""
Project wide conf options. It is a singleton object
"""
@Singleton
class Conf():
    def __init__(self):
        logging.debug("Conf object is initializing")
        # Ntpd()  # Update current time with Ntpd
        self.APP_REL_VERSION = "V.0.1.2"
        self.APP_REL_DATE = "28.02.2016"
        self.BUCKET_ID = RpSerial().bucket_id()
        self.MAX_TAG_READ_CNT = 5  # Max number of tries before quitting tag read sequence
        self.CAMERA_ENABLED = True  # Camera and picture capture can be disables in runtime

        if self.BUCKET_ID != "ERROR000000000" and self.BUCKET_ID != "0000000000000000":
            self.RFID_APP = "./helpers/exathing"
            self.SNAPSHOT_APP = "./helpers/snapshot.sh"
            self.RFID_DEVICE = "tmr:///dev/ttyAMA0"
            self.GPS_DEVICE = "/dev/ttyUSB0"
            self.SQLITE_DB = DiskMount().get_mount_path() + "/logdb"
            self.SQLITE_TMP_DB = "/tmp/logdb"
            self.APP_SERVER = 'http://demo.io'
            self.CAFILE = '/Users/keys/demo.pem'
            self.CAPTURED_SNAPSHOT = '/tmp/tag.jpg'
            self.APP_MODE = "Production"
        else:
            if g_test_mode == "mac":
                self.APP_SERVER = 'http://localhost:8081'
                self.SQLITE_DB = "/opt/local/var/logdb"
                self.APP_MODE = "Test_Mac"
                logging.info("Will run in local test mode")
            else:
                self.APP_SERVER = 'https://demo.io'
                self.SQLITE_DB = "/tmp/logdb"
                self.APP_MODE = "Test_Aws"
                logging.info("Will run in aws server test mode")

            self.RFID_APP = "uname"
            self.SNAPSHOT_APP = "ls" # TODO: Find an app for PC demo
            self.RFID_DEVICE = "-n"
            self.GPS_DEVICE = "/dev/null"
            self.SQLITE_TMP_DB = "/tmp/logdb"
            self.CAFILE = '/Users/keys/demo.pem'
            self.CAPTURED_SNAPSHOT = '/tmp/tag.jpg'

        logging.debug("Conf object is initialized")


if __name__ == '__main__':
    import sys

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    sql_db = Conf.Instance().SQLITE_DB
    logging.debug(sql_db)
