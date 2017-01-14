import logging
import subprocess
import datetime


"""
    Class implementation for updating time with ntpd servers with big jump
"""
class Ntpd():
    def  __init__(self):
        time_ok = False
        try_cnt = 0
        while not time_ok and try_cnt < 5:
            try_cnt += 1
            time_ok = self.test()
            if not time_ok:
                logging.info("Updating time - try cnt: %d", try_cnt)
                self.update()

    def update(self):
        try:
            subprocess.check_output(["./helpers/ntpd.sh"])
        except Exception as e:
            logging.error(e)
            logging.error("Failed in updating time.")
        else:
            return True

        return False

    def test(self):
        logging.info("Testing if current time is newer than 01.01.2015 ")

        new_time = datetime.datetime.now()
        test_time = datetime.datetime(2015, 1, 1)
        if new_time > test_time:
            return True
        return False


if __name__ == '__main__':
    import sys

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    Ntpd()
    logging.debug("Current date - time: %s", datetime.datetime.now())
