import logging
import time
import Queue
import threading

try:
    import RPi.GPIO as GPIO
except ImportError:
    import fakes.fakegpio as GPIO

"""
    Threaded class  which produce buzzer sound

    @param none
"""
class BuzzerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(23, GPIO.OUT)
        self.m_process_queue = Queue.Queue()

    def _beep_ok(self):
        logging.debug("Beep ok callback called")
        try:
            GPIO.output(23, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(23, GPIO.LOW)
        except:
            raise
        finally:
            GPIO.output(23, GPIO.LOW)

    def _beep_nok(self):
        logging.debug("Beep nok callback called")
        try:
            GPIO.output(23, GPIO.HIGH)
            time.sleep(2)
            GPIO.output(23, GPIO.LOW)
        except:
            raise
        finally:
            GPIO.output(23, GPIO.LOW)

    def _execute_from_queue(self):
            cb_fn = self.m_process_queue.get()
            try:
                cb_fn()

            except Exception as e:
                logging.error("Exception")
                logging.error(e)
                raise

            self.m_process_queue.task_done()

    def run(self):
        while True:
            self._execute_from_queue()

    def start(self):
        super(BuzzerThread, self).setDaemon(True)
        super(BuzzerThread, self).start()

    def beep_ok(self):
        self.m_process_queue.put(self._beep_ok)

    def beep_nok(self):
        self.m_process_queue.put(self._beep_nok)


if __name__ == '__main__':
    import sys

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    buzzer = BuzzerThread()
    buzzer.start()
    while True:
        logging.debug("Beep OK")
        buzzer.beep_ok()
        time.sleep(10)
        logging.debug("Beep NOK")
        buzzer.beep_nok()
        time.sleep(10)
