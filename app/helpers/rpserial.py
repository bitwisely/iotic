import logging

"""
    Class implementation for unique serial ID for the raspberry module.
"""
class RpSerial():
    def __init__(self):
      # Extract serial from cpuinfo file
      self.m_cpuserial = "0000000000000000"
      try:
        f = open('/proc/cpuinfo','r')
        for line in f:
          if line[0:6]=='Serial':
            self.m_cpuserial = line[10:26]
        f.close()
      except:
        self.m_cpuserial = "ERROR000000000"

    def bucket_id(self):
        return self.m_cpuserial


if __name__ == '__main__':
    rps = RpSerial()
    logging.debug("Bucket ID:", rps.bucket_id())