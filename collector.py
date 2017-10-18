# sys
import sys

# DeviceManager
from device.device_manager import DeviceManager
from device.device_manager import DeviceVIDPIDList

if __name__ == '__main__':

    # load VIDs and PIDs from config.ini
    vid_pid_list = DeviceVIDPIDList('config.ini')

    # instantiate device_manager
    dev_man = DeviceManager(vid_pid_list)

    try:
        # run the device manager
        dev_man.run()
    except KeyboardInterrupt:
        dev_man.stop_all_devices()
        sys.exit(0)
