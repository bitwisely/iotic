import threading

"""
    Threaded class which monitor all services health, recover from failure if possible, reports to server and
    restarts App

    TODO: implement

    @param service_objs
"""
class MonitorThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.m_app = app