import logging
import time
import Queue
import threading
import os
import subprocess

from conf import Conf

"""
    Threaded class which takes pictures of tags

    @param none
"""
class CameraThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.m_process_queue = Queue.Queue()
        self.m_conf = Conf.Instance()
        self._init_camera()

    def _init_camera(self):
        pass

    def _take_picture(self):
        try:
            logging.debug("Remove old picture")
            os.remove(self.m_conf.CAPTURED_SNAPSHOT)
        except OSError:  # File does not exist case
            pass

        logging.debug("Take picture.")
        subprocess.check_output([self.m_conf.SNAPSHOT_APP])

        # If picture exists send False, True otherwise to catch the error
        return not os.path.isfile(self.m_conf.CAPTURED_SNAPSHOT)


    def _execute_from_queue(self):
            cb_fn = self.m_process_queue.get()
            try:
                err = self._take_picture()
                cb_fn(err)

            except Exception as e:
                logging.error("Exception")
                logging.error(e)
                raise

            self.m_process_queue.task_done()

    def run(self):
        while True:
            self._execute_from_queue()

    def start(self):
        super(CameraThread, self).setDaemon(True)
        super(CameraThread, self).start()

    # API for camera thread

    def take_picture(self, cb):
        self.m_process_queue.put(cb)

    def restart(self):
        self._init_camera()

    def close(self):
        logging.debug("Closing camera")
        self.m_camera.close()
        self.m_camera = None

if __name__ == '__main__':
    import sys

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    def picture_ready():
        logging.debug("Picture is ready.")

    camera = CameraThread()
    camera.start()

    try:
        while True:
            logging.debug("Take picture")
            camera.take_picture(picture_ready)
            time.sleep(10)
    
    except:
        logging.debug("\nKilling Thread...")
        camera.close()
        logging.debug("Done.\nExiting.")
