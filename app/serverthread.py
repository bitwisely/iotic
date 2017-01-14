import logging
import Queue
import threading
import datetime
import time
import requests

from conf import Conf
from sqliteserializer import SqliteSerializer


"""
    Threaded class  which sends data to web server which is pushed to its process queue. If sending to server fails,
    it stores message in SQLite.

    @param SQlite storage object
"""
class ServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.m_conf = Conf.Instance()
        self.m_process_queue = Queue.Queue()
        self.m_server_status = False
        self.m_sqlite_serializer = SqliteSerializer()
        self.m_bucket_id = self.m_conf.BUCKET_ID
        self._check_server()

    def _check_server(self):
        msg = {'method': 'GET',
               'url': self.m_conf.APP_SERVER,
               'api_path': '/api/emb/health',
               'type': "msg"}
        try:
            r = requests.get(msg['url'] + msg['api_path'], timeout=10, verify=self.m_conf.CAFILE)
            if r.status_code == 200:
                self.m_server_status = True
            else:
                logging.warning("Server status : %d", r.status_code)
                self.m_server_status = False

        except Exception as e:
            logging.warning("Exception")
            logging.warning(e)
            self.m_server_status = False

    def _send_to_persistent_storage(self, msg):
        self.m_server_status = False
        self.m_sqlite_serializer.append(msg)

    def _log(self, msg):
        payload = {'method': 'POST',
                   'url': self.m_conf.APP_SERVER,
                   'api_path': '/api/emb/log',
                   'data': {"msg": msg,
                            "date": int(datetime.datetime.now().strftime("%s")) * 1000,
                            "bucketID": self.m_bucket_id},
                   'type': "log"}
        if not self.m_server_status:
            self._send_to_persistent_storage(payload)
            return {}

        return payload

    def _execute_from_queue(self):
        try:
            msg = self.m_process_queue.get(False)
        except Queue.Empty:
            pass
        else:
            try:
                if self.m_server_status:
                    print (msg['method'])
                    print (msg['api_path'])
                    print (msg['data'])
                    if msg['method'] == 'POST':
                        r = requests.post(msg['url'] + msg['api_path'], data=msg['data'], timeout=10, verify=self.m_conf.CAFILE)

                        if r.status_code != 200 and msg["type"] == "msg":
                            logging.warning("POST error %d", r.status_code)
                            self._send_to_persistent_storage(msg)

                    elif msg['method'] == 'POST_MULTI_PART':
                        # Try to load the file
                        try:
                            files = {'file': open(msg['file_path'], 'rb')}
                        except:
                            files = {'file': None}
                        r = requests.post(msg['url'] + msg['api_path'], data=msg['data'], files=files, timeout=10, verify=self.m_conf.CAFILE)

                        if r.status_code != 200 and msg["type"] == "msg":
                            logging.warning("POST error %d", r.status_code)
                            self._send_to_persistent_storage(msg)
                            if msg['callback'] is not None:
                                msg['callback'](True, "hello")  # Handle next actions for a failed multi-part post
                        else:
                            if msg['callback'] is not None:
                                msg['callback'](False, "hello")  # Handle next actions for a successful multi-part post

                        # Close the file
                        files['file'].close()

                    elif msg['method'] == 'GET':
                        if 'params' in msg.keys():
                            r = requests.get(msg['url'] + msg['api_path'], params=msg['params'], timeout=10, verify=self.m_conf.CAFILE)
                        else:
                            r = requests.get(msg['url'] + msg['api_path'], timeout=10, verify=self.m_conf.CAFILE)

                        if r.status_code != 200 and msg["type"] == "msg":
                            logging.warning("GET error %d", r.status_code)
                            self._send_to_persistent_storage(msg)

                else:
                    self._send_to_persistent_storage(msg)
                    self._check_server()

            except Exception as e:
                if msg and msg["type"] and msg["type"] == "msg":
                    logging.warning("Exception")
                    logging.warning(e)
                    self._send_to_persistent_storage(msg)
                    self._log(e)

            self.m_process_queue.task_done()

    def _consume_sqlite_store(self):
        if self.get_server_status():
            json_data = self.m_sqlite_serializer.popleft(False)

            if json_data:
                logging.info(json_data)
                self.m_process_queue.put(json_data)

    def get_server_status(self):
        return self.m_server_status

    def run(self):
        que_counter = 0
        while True:
            time.sleep(0.1)
            self._execute_from_queue()
            if que_counter % 10 == 0:
                self._consume_sqlite_store()
            if que_counter > 1000:
                que_counter = 0
            else:
                que_counter += 1

    def start(self):
        super(ServerThread, self).setDaemon(True)
        super(ServerThread, self).start()

    # API START

    # RFID reads for each tag
    def post_tag_data(self, json_data, cb=None):
        logging.info("Send tag read data to server")
        self.m_process_queue.put({'method': 'POST',
                                  'data': json_data,
                                  'callback': cb,
                                  'url': self.m_conf.APP_SERVER,
                                  'api_path': '/api/emb/tag',
                                  'type': "msg"})

    # Tag picture
    def post_tag_picture(self, json_data, file_path, cb=None):
        logging.error("Send tag picture to server")
        self.m_process_queue.put({'method': 'POST_MULTI_PART',
                                  'data': json_data,
                                  'file_path': file_path,
                                  'callback': cb,
                                  'url': self.m_conf.APP_SERVER,
                                  'api_path': '/api/emb/tag/picture',
                                  'type': "msg"})

    # Bucket related data
    def post_bucket_data(self, json_data, cb=None):
        logging.info("Send bucket position to server")
        self.m_process_queue.put({'method': 'POST',
                                  'data': json_data,
                                  'callback': cb,
                                  'url': self.m_conf.APP_SERVER,
                                  'api_path': '/api/emb/bucket',
                                  'type': "msg"})

    # Send log messages to server
    def post_log_msg(self, msg):
        json_data = self._log(msg)
        if json_data != {}:
            self.m_process_queue.put(json_data)
        else:
            logging.warning("Log message %s is stored in persistent storage ", msg)


if __name__ == '__main__':
    from helpers.test_setup import setup_fixture

    import sys
    import time


    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    tag_data = {'bucketID': 'BUCKET123',
                  'tagID': 'TAG123',
                  'lat': '30.123',
                  'long': '40.123',
                  'date': int(datetime.datetime.now().strftime("%s")) * 1000,
                  'pictureID': "PICTURE123"}

    tag_picture_data = {'pictureID': "PICTURE123"}

    bucket_data = {'lat': 0,
                  'long': 1,
                  'utc': "7 June 2015",
                  'time': 97879879,
                  'date': int(datetime.datetime.now().strftime("%s")) * 1000,
                  'speed': 10,
                  'alt': 10,
                  'bucketID': 79879}

    try:
        def _picture_cb(err, resp):
            if err:
                logging.error('ERROR')
                logging.error(resp)
            else:
                logging.debug('RESP')
                logging.debug(resp)

        setup_fixture()

        t = ServerThread()
        t.start()
        while True:
            t.post_log_msg("This is a test log message")
            t.post_bucket_data(bucket_data)
            t.post_tag_data(tag_data)
            t.post_tag_picture(tag_picture_data, Conf.Instance().CAPTURED_SNAPSHOT, _picture_cb)
            time.sleep(2)

    except (KeyboardInterrupt, SystemExit):  # When you press ctrl+c
        logging.debug("\nKilling Thread...")
        t.running = False
        t.m_process_queue.join() # wait for the queue to finish what it's doing
        t.join() # wait for the thread to finish what it's doing
        logging.debug("Done.\nExiting.")
