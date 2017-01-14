"""
    Complete API tests
"""
from __future__ import division

from ..app.conf import Conf
from ..app.serverthread import ServerThread
from ..app.rfidreaderthread import RfIDReaderThread
from ..app.helpers.test_setup import setup_fixture

if Conf.Instance().CAMERA_ENABLED:
    from ..app.camerathread import CameraThread

import os
import sys
import time
import datetime
import logging
import random

from shapely.geometry import LineString

path_0 = LineString([(10, 20), (50, 60), (80, 30), (40, 10), (10, 20)])
path_1 = LineString([(0, 0), (-50, -60), (-80, -30), (-40, -10), (0, 0)])
path_2 = LineString([(5, 5), (30, 60), (40, 80), (30, 50), (5, 5)])
path_3 = LineString([(8, 20), (10, 40), (30, 30), (60, 40), (8, 20)])
path_4 = LineString([(-10, -20), (0, 20), (30, 40), (0, 30), (-10, -20)])
path_5 = LineString([(-10, 20), (10, 0), (20, 20), (-40, 10), (-10, 20)])
path_6 = LineString([(50, 20), (50, 40), (60, 20), (60, 0), (50, 20)])
path_7 = LineString([(30, 20), (30, 30), (40, 50), (40, 20), (30, 20)])
path_8 = LineString([(-30, 20), (-30, 30), (-40, 50), (-40, 20), (-30, 20)])
path_9 = LineString([(-30, -20), (-30, -30), (-40, -50), (-40, -20), (-30, -20)])

paths = [path_0, path_1, path_2, path_3, path_4, path_5, path_6, path_7, path_8, path_9]


def generate_buckets(latitude, longtitude):
    buckets = []
    for i in range(0, 10):
        test_bucket = {}
        tmp_lat = latitude + 0.02 * random.uniform(0, 1)
        tmp_long = longtitude + 0.02 * random.uniform(0, 1)

        test_bucket.update({'m_json':{'lat': tmp_lat,
            'long': tmp_long,
            'utc': "7 Haziran 2015",
            'time': 97879879,
            'date': int(datetime.datetime.now().strftime("%s")) * 1000,
            'speed': 10,
            'alt': 10,
            'bucketID': i}})

        test_bucket.update({'m_lat': tmp_lat})
        test_bucket.update({'m_long': tmp_long})
        test_bucket.update({'m_line': paths[i]})
        test_bucket.update({'m_cur_length': 0})
        buckets.append(test_bucket)

    return buckets

if __name__ == '__main__':
    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)
    setup_fixture()
    test_buckets = generate_buckets(38.453347, 27.210071)  # Izmir - Bornova

    try:
        server = ServerThread()
        server.post_log_msg("TEST_STARTED")
        reader = RfIDReaderThread()

        if Conf.Instance().CAMERA_ENABLED:
            camera = CameraThread()
        else:
            camera = None

        server.start()
        reader.start()

        if camera:
            camera.start()

        while True:
            for bucket in test_buckets:
                # Send bucket position for each bucket
                server.post_bucket_data(bucket['m_json'])
                pt = bucket['m_line'].interpolate(bucket['m_cur_length']/bucket['m_line'].length, True)
                bucket['m_json']['long'] = bucket['m_long'] + 0.0003 * pt.y
                bucket['m_json']['lat'] = bucket['m_lat'] + 0.0003 * pt.x
                bucket['m_json']['date'] = (int(datetime.datetime.now().strftime("%s")) + 30) * 1000  # Add 30 seconds
                bucket['m_cur_length'] += 1
                if bucket['m_cur_length'] >= bucket['m_line'].length:
                    bucket['m_cur_length'] = 0

                # Callback function for complete camera snapshots.
                def _capture_cb(err):
                    if err:
                        logging.error("Could not capture tag picture")
                    else:
                        data = {'pictureID': "TODO_IMPLEMENT"}
                        print("Hello world.")
                        tag_pic = {'picture': open(Conf.Instance().CAPTURED_SNAPSHOT, 'rb')},
                        server.post_tag_picture(data, tag_pic)

                # Callback function for completed RFID reads
                def _reader_cb(err, tag_id):
                    if err:
                        logging.warning(tag_id)

                    data = {'bucketID': bucket['m_json']['bucketID'],
                    'tagID': 'TR' + str(bucket['m_json']['bucketID']) + 'ID' + str(bucket['m_cur_length']),
                    'lat': bucket['m_json']['lat'],
                    'long': bucket['m_json']['long'],
                    'date': bucket['m_json']['date'],
                    'pictureID': "TODO_IMPLEMENT"}
                    server.post_tag_data(data)

                    if camera:
                        camera.take_picture(_capture_cb)

                if bucket['m_cur_length'] % 10 == 0:
                    reader.read(_reader_cb)

                time.sleep(0.1)

            time.sleep(2)

    except (KeyboardInterrupt, SystemExit): # when you press ctrl+c
        logging.debug("\nKilling Thread...")
        server.post_log_msg("TEST_STOPPED")
        reader.running = False
        reader.m_process_queue.join()  # wait for the queue to finish what it's doing
        reader.join()  # wait for the thread to finish what it's doing
        server.running = False
        server.m_process_queue.join()  # wait for the queue to finish what it's doing
        server.join()  # wait for the thread to finish what it's doing
        logging.debug("Done.\nExiting.")
