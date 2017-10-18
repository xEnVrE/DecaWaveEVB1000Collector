# pyserial
import serial
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo
from serial.serialutil import SerialException

# make ListPortInfo hashable
def hash_fun(self):
    return hash(str(self))
ListPortInfo.__hash__ = hash_fun

# multi-threading
from threading import Lock
from threading import Thread

# sleep
from time import sleep

# sys
import sys
import errno

# EVB1000 decoder
from device.decoder import DataFromEVB1000
from device.decoder import InvalidDataFromEVB1000

# CSV logger
from output.csv_logger import CSVLogger

# csv required by class DeviceVIDPIDList
import csv

class Device(Thread):
    """
    Represents an EVB1000 Tag connected through a serial port.

    Inherits from Thread to handle serial i/o operations
    in background.
    """
    def __init__(self, port):
        # call Thread constructor
        Thread.__init__(self)
        
        # save port
        self.port = port

        # configure device
        self.configure()

        # set device state
        self._state = 'running'
        self.state_lock = Lock()

        # set device id
        self.id = str(hash(self.port))

        # data
        self._last_data = None
        self.data_lock = Lock()

        # instantiate a new csv logger
        self._logger = CSVLogger()

    def __str__(self):
        return self.port.device

    @property
    def logger(self):
        return self._logger

    @property
    def last_data(self):
        self.data_lock.acquire()

        data = self._last_data
        
        self.data_lock.release()

        return data

    @last_data.setter
    def last_data(self, data):
        self.data_lock.acquire()

        self._last_data = data
        
        self.data_lock.release()
        
    @property
    def state(self):
        self.state_lock.acquire()
        value = self._state
        self.state_lock.release()
        
        return self._state

    @state.setter
    def state(self, new_state):
        self.state_lock.acquire()
        self._state = new_state
        self.state_lock.release()

    def stop_device(self):
        """
        Change the state of the device from 'running' to 'stopped'.
        """

        self.state = 'stopped'

    def run(self):
        """
        Thread main method.
        """

        # gracefully stop thread if the connection is not working
        # TODO: signal the GUI that an I/O error occured
        if not self.connect():
            return
        
        while self.state == 'running':
            try:
                # attempt reception of a new line
                line = self.serial.readline()

                # process only non null data
                if len(line) > 0:

                    # store new line received
                    # access to last_data here may happen *before*
                    # the GUI has requested the data related to the last
                    # signal emission. In this case the old line is overwritten
                    # by the new one.
                    #
                    # TODO: consider a buffered approach
                    #
                    
                    # decode last line received if possible
                    try:
                        evb1000_data = DataFromEVB1000(line)
                    except InvalidDataFromEVB1000:
                        # ignore this line
                        continue

                    # continue only if message type was decoded successfully
                    if evb1000_data.msg_type_decoded:
                        # store data
                        self.last_data = evb1000_data.decoded

                        # signal the GUI that new data is available
                        self.new_data_available.emit(self.id)

                        # log to file
                        self.logger.log_data(evb1000_data)

            except SerialException:
                pass

        if self.state == 'stopped':
            # close csv file
            self.logger.close()
            
            # stop thread
            self.close()

    def configure(self):
        """
        Get a serial.Serial instance and configure it.
        """

        # instantiate Serial
        self.serial = serial.Serial()

        # set port_path, e.g. '/dev/ttyUSBx' or 'COMx'
        self.serial.port = self.port.device

        # set baudrate
        self.serial.baudrate = 115200

    def connect(self):
        """
        Open the serial port.

        return Serial.is_open
        """

        # in Windows even if the device is detected it
        # may be not ready to be opened yet
        while not self.serial.is_open:
            try:
                self.serial.open()
            except SerialException:
                pass
            
        return True

    def close(self):
        """
        Close the serial port.

        return Serial.is_open
        """

        self.serial.close()

class MalformedConfigurationFile(Exception):
        pass

class DeviceVIDPIDList:
    """
    Store VIDs and PIDs for devices that are part of the EVB1000 system.
    """

    def __init__(self, filename):

        # filename of the configuration file
        self.filename = filename
        
        # empty list of ids
        self.vid_pid_s = []

        # load VIDs and PIDs from file
        self.load_from_file()

    def get_vid_pid_list(self):
        """
        Return the list containing the valid VIDs and PIDs
        """

        return self.vid_pid_s

    def load_from_file(self):
        """
        Load VIDs and PIDs from file
        """

        # if state = 0 the function checks if
        # the file starts with the string CONFIG_VID_PID
        state = 0

        try: 
            with open(self.filename, 'r') as csvfile:
                reader = csv.reader(csvfile, delimiter=' ')
                for row in reader:

                    # checks if the file starts with CONFIG_VID_PID
                    if state == 0:
                        if not (row[0] == 'CONFIG_VID_PID'):
                            raise MalformedConfigurationFile
                        else:
                            # go to next step, i.e., checking the header of the file
                            state = state + 1
                            
                    # checks if the header is of the form 'VID PID'
                    elif state == 1:
                        if not (row[0] == 'VID' and row[1] == 'PID'):
                            raise MalformedConfigurationFile
                        else:
                            # go to next step, i.e., reading tuples of VIDs and PIDs
                            # if they are valid
                            state = state + 1

                    # read and store tuples of VIDs and PIDs, if they are valid
                    else:
                        # extract VID and PID
                        vid = row[0]
                        pid = row[1]
                        
                        # check if the row contains a 4 characters long VID and
                        # a 4 characters long PID
                        if (len(row[0]) != 4) or (len(row[1]) != 4):
                            raise MalformedConfigurationFile

                        # store (VID, PID) pair
                        self.vid_pid_s.append((vid,pid))
        
        except (OSError, IOError) as e:
            if getattr(e, 'errno', 0) == errno.ENOENT:
                print('Error: Configuration file ' + self.filename + ' not found.')
                sys.exit(1)
        except MalformedConfigurationFile:
            print('Error: Malformed configuration file ' + self.filename + '.')
            sys.exit(1)

        # if no (VID, PID) tuples were found exit
        if len(self.vid_pid_s) == 0:
            print('Error: No (VID, PID) entries found in ' + self.filename + '.')
            sys.exit(1)
              
class DeviceManager():
    """
    Manage EVB1000 devices connected through a serial port.
    """
    
    def __init__(self, vid_pid_list):
        # empty list of ports
        self.connected_ports = []

        # empty dictionary of devices
        self.configured_devices = dict()

        # empty list of *newly* configured devices
        self._new_devices = []
        # empty list of *just* removed  devices
        self._removed_devices = []

        # store list of PIDs and VIDs of devices belonging to the EVB1000 system
        self.target_vid_pid = vid_pid_list.get_vid_pid_list()

    @property
    def new_devices(self):

        # copy new devices
        devs = self._new_devices

        # clean _new_devices
        self._new_devices = []
        
        return devs

    @new_devices.setter
    def new_devices(self, devs):
        self._new_devices = devs

    @property
    def removed_devices(self):

        # copy new devices
        devs = self._removed_devices

        # clean _new_devices
        self._removed_devices = []
        
        return devs

    @removed_devices.setter
    def removed_devices(self, devs):
        self._removed_devices = devs

    def device(self, device_id):
        return self.configured_devices[device_id]
    
    def run(self):
        """
        Device Manager main method.
        """

        while True:
            # update new and removed ports
            new_ports, removed_ports = self.update_ports()
                
            # in case of new ports
            if new_ports:

                # configure devices connected to ports in new_ports
                self.new_devices = self.configure_devices(new_ports)

                # signal GUI that new devices are available
                self.new_dev_connected_sig.emit()

            # in case of removed ports
            if removed_ports:
                # removed devices that were disconnected
                self.removed_devices = self.remove_devices(removed_ports)

                # signal GUI that some devices were removed
                self.dev_removed_sig.emit()

            # wait some time
            sleep(1)

    def configure_devices(self, ports):
        """
        Configure devices connected via serial ports in ports.

        Return a list containing the new devices.
        """

        new_devices = []
        
        # for each port create a new Device and start the underlying thread
        for p in ports:
            new_device = Device(p)
            self.configured_devices[new_device.id] = new_device
            new_devices.append(new_device)
            new_device.start()

        return new_devices

    def remove_devices(self, ports):
        """
        Remove devices whose ports were removed.

        Return a list containing the removed devices.
        """

        removed_devices = []

        # for each port change the state of the underlying thread
        # from 'running' to 'stopped' using stop_device()
        for p in ports:
            # device id is defined as str(port.__hash__())
            device_id = str(hash(p))
            self.configured_devices[device_id].stop_device()
            
            # clean configured_devices dict
            removed_device = self.configured_devices.pop(device_id)
            removed_devices.append(removed_device)

        return removed_devices

    def stop_all_devices(self):
        """
        Stop all devices.
        """
        # stop devices
        for device_id in self.configured_devices:
            self.configured_devices[device_id].stop_device()

        # wait for thread end
        for device_id in self.configured_devices:
            self.configured_devices[device_id].wait()


    def update_ports(self):
        """
        Update list of serial ports connected.

        New ports are added to connected_ports if the underlying
        usb device match the target VID and PID.
        Missing ports are remove from connected_ports.

        Return a list containing new ports.
        Return a list containing removed ports.
        """
        
        # fetch only those ports having
        # VID:PID == a valid (VID, PID) pair in target_vid_pid
        ports = []

        for valid_pair in self.target_vid_pid:
            vid_pid = valid_pair[0] + ':' + valid_pair[1]
            ports = ports +  [p for p in list_ports.grep(vid_pid)]
        #ports = list_ports.comports()
        
        # add new ports to connected_ports
        # and update new_ports
        new_ports = []
        for p in ports:
            if not p in self.connected_ports:
                self.connected_ports.append(p)
                new_ports.append(p)

        # remove missing ports from devices_found
        # and update removed_ports
        removed_ports = []
        for p in self.connected_ports:
            if not p in ports:
                self.connected_ports.remove(p)
                removed_ports.append(p)

        return new_ports, removed_ports

