import logging
import os
import sqlite3
import datetime
from cPickle import loads, dumps
from time import sleep
from conf import Conf

try:
    from thread import get_ident
except ImportError:
    from dummy_thread import get_ident


MAX_ERROR_IN_OPERATION = 3

"""
    SQlite message queue implementation
"""
class SqliteSerializer(object):

    _create = (
            'CREATE TABLE IF NOT EXISTS queue '
            '('
            '  id INTEGER PRIMARY KEY AUTOINCREMENT,'
            '  item BLOB'
            ')'
            )
    _count = 'SELECT COUNT(*) FROM queue'
    _iterate = 'SELECT id, item FROM queue'
    _append = 'INSERT INTO queue (item) VALUES (?)'
    _write_lock = 'BEGIN IMMEDIATE'
    _popleft_get = (
            'SELECT id, item FROM queue '
            'ORDER BY id LIMIT 1'
            )
    _popleft_del = 'DELETE FROM queue WHERE id = ?'
    _peek = (
            'SELECT item FROM queue '
            'ORDER BY id LIMIT 1'
            )

    def __init__(self):
        # TODO: I need to find a way to post message from files to server
        # self.m_server = ServerThread.Instance()
        self.m_conf = Conf.Instance()
        self.m_valid_sqlite_instance = True
        self.m_sqlite_path = self.m_conf.SQLITE_DB
        self.m_error_cnt = 0

        if not self._init_connection(self.m_sqlite_path):

            # If init operation fails try to remove SQLITE-DB file
            try:
                os.remove(self.m_sqlite_path)
            except Exception as e:  # File does not exist case
                pass

            logging.error("SQLDB init first try failed")
            logging.warning("Tried to recover with removing SQLDB file.")
            # self.m_server.post_log_msg("SQLITE_INIT_FAILED_FOR_FIRST_TIME")

            # Re-try to generate SQLITE-DB
            if not self._init_connection(self.m_sqlite_path):
                logging.error("SQLDB init second try failed")
                logging.warning("Trying SQLDB file generation in tmp folder.")
                # self.m_server.post_log_msg("SQLITE_INIT_FAILED_FOR_SECOND_TIME")
                # self.m_server.post_log_msg("TRYING_SQLITE_IN_TMP_FOLDER")
                self.m_sqlite_path = self.m_conf.SQLITE_TMP_DB
                if not self._init_connection(self.m_sqlite_path):
                    # Give up.
                    # self.m_server.post_log_msg("SQLITE_SUPPORT_DISABLED")
                    logging.error("SQLDB init third try failed, giving up!")
                    self.m_valid_sqlite_instance = False

    def _init_connection(self, path):
        try:
            logging.info("Path to SqLite: %s", path)
            self.path = os.path.abspath(path)
            self._connection_cache = {}
            with self._get_conn() as conn:
                conn.execute(self._create)

            # Test system during init

            # Append a test string "init_test"
            payload = {'method': 'POST',
                       'url': self.m_conf.APP_SERVER,
                       'api_path': '/api/emb/log',
                       'data': {"msg": "startup_sqlite_test",
                                "date": int(datetime.datetime.now().strftime("%s")) * 1000,
                                "bucketID": self.m_conf.BUCKET_ID},
                       'type': "log"}
            obj_buffer = buffer(dumps(payload, 2))
            with self._get_conn() as conn:
                conn.execute(self._append, (obj_buffer,))

            # If all goes well this means we have a running SqliteDB instance
            return True

        except Exception as e:
            logging.error("Exception")
            logging.error(e)
            return False

    def __len__(self):
        with self._get_conn() as conn:
            l = conn.execute(self._count).next()[0]
        return l

    def __iter__(self):
        with self._get_conn() as conn:
            for id, obj_buffer in conn.execute(self._iterate):
                yield loads(str(obj_buffer))

    def _get_conn(self):
        id = get_ident()
        if id not in self._connection_cache:
            self._connection_cache[id] = sqlite3.Connection(self.path,
                    timeout=60)
        return self._connection_cache[id]

    def append(self, obj):
        try:
            if not self.m_valid_sqlite_instance:
                return

            obj_buffer = buffer(dumps(obj, 2))
            with self._get_conn() as conn:
                conn.execute(self._append, (obj_buffer,))

            # If we can reach here means we can store
            self.m_error_cnt = 0

        except Exception as e:
            logging.error("Exception")
            logging.error(e)

            # Increment consecutive errors count
            self.m_error_cnt += 1
            if self.m_error_cnt >= MAX_ERROR_IN_OPERATION:
                # If append operation fails max allowed times try to remove SQLITE-DB file
                logging.warning("Delete corrupted Sqlite file")
                # self.m_server.post_log_msg("CORRUPTED_SQLITE_FILE_REMOVED")
                try:
                    os.remove(self.m_sqlite_path)
                except Exception as e:
                    pass


    def popleft(self, sleep_wait=True):
        try:
            if not self.m_valid_sqlite_instance:
                return None

            keep_pooling = True
            wait = 0.1
            max_wait = 2
            tries = 0
            with self._get_conn() as conn:
                id = None
                while keep_pooling:
                    conn.execute(self._write_lock)
                    cursor = conn.execute(self._popleft_get)
                    try:
                        id, obj_buffer = cursor.next()
                        keep_pooling = False
                    except StopIteration:
                        conn.commit() # unlock the database
                        if not sleep_wait:
                            keep_pooling = False
                            continue
                        tries += 1
                        sleep(wait)
                        wait = min(max_wait, tries/10 + wait)
                if id:
                    conn.execute(self._popleft_del, (id,))
                    return loads(str(obj_buffer))

        except Exception as e:
            logging.error("Exception")
            logging.error(e)

        return None

    def peek(self):
        try:
            if not self.m_valid_sqlite_instance:
                return None

            with self._get_conn() as conn:
                cursor = conn.execute(self._peek)
                try:
                    return loads(str(cursor.next()[0]))
                except StopIteration:
                    return None

        except Exception as e:
            logging.error("Exception")
            logging.error(e)

        return None


if __name__ == '__main__':
    from random import random
    import sys

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    # Log options: debug, info, warning, error and critical
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    class FakeServer():
        def __init__(self):
            pass

        def post_log_msg(self, msg):
            logging.info(msg)


    Server = FakeServer()
    q = SqliteSerializer(Server)

    for i in range(1, 10):
        tmp = random()
        logging.debug("%s: %s", i, tmp)
        q.append(str(tmp))

    for i in range(1, 150):
        val = q.popleft(False)
        logging.debug("%s: %s", i, val)