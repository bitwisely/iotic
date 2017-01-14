import logging
import subprocess
import os

"""
    Class implementation for finding and mounting logger USB disk
"""
class DiskMount():
    def __init__(self):
        self.m_mount_path = "/media/usbDISK"
        self.m_device_list = self.get_device_list()
        if self.mount(self.m_device_list, self.m_mount_path):
            self.test()

    def get_device_list(self):
        device_list = []
        all_list = subprocess.check_output(["ls", "/dev"]).split()
        for item in all_list:
            if "sd" in item:
                device_list.append(item)
        return device_list

    def mount(self, device_list, mount_path):
        for device in device_list:
            try:
                subprocess.check_output(["./helpers/mount_usb.sh", device, mount_path])
            except:
                self.m_mount_path = "/tmp"
                logging.error("Failed in mounting USB disk. Device mount point is now %s", self.m_mount_path)
            else:
                self.m_mount_path = "/media/usbDISK"
                logging.info("Mount OK with device: %s, path: %s", device, self.m_mount_path)
                return True
        return False

    def test(self):
        try:
            logging.debug("Testing USB disk")

            # Generate test file
            open(self.m_mount_path + "/test.txt", 'w').close()

            # Remove test file
            try:
                os.remove(self.m_mount_path + "/test.txt")
            except OSError:  # File does not exist case
                pass

            logging.info("Testing USB disk passed.")

        except Exception as e:
            logging.error("Exception")
            logging.error(e)
            self.m_mount_path = "/tmp"
            logging.error("Failed in USB disk test. Device mount point is now %s", self.m_mount_path)

    def get_mount_path(self):
        return self.m_mount_path

if __name__ == '__main__':
    import sys

    FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s() ] %(message)s"
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format=FORMAT)

    dm = DiskMount()
    logging.debug("Mount path: %s", dm.get_mount_path())
