import csv
import time

# EVB1000 decoder
from device.decoder import DataFromEVB1000

class CSVLogger:
    """
    Save data from the EVB1000 serial to a csv files.
    """

    def __init__(self):

        # empty dictionary of file descriptors
        self.files = dict()

        # empty ditionary of writers
        self.writers = dict()

        # set state to disabled
        self._enabled = False

        # list of allowed message types
        self.allowed_msg_types = ['tpr', 'kmf', 'apr',\
                                  'arr', 'trr']
    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, state):
        self._enabled = state

    def create_file_name(self, msg_type, device_id):
        """
        Generate the filename depending on the msg_type and the device ID.
        """

        filename = ''
        
        if msg_type == 'tpr' or msg_type == 'apr' or msg_type == 'trr':
            filename = "tag_" + str(device_id) + "_" +\
                       time.strftime("%d_%m_%Y") + "_" + str(msg_type)
        # maintain compatibility with MATLAB collection facilities
        elif msg_type == 'arr':
            filename = 'a2a_anch_' + str(device_id)

        return filename
        
    def log_data(self, evb1000_data):
        """
        Log new line from EVB1000 serial line.
        """

        # log only if the logger is enabled
        if not self.enabled:
            return

        # extract data
        data = evb1000_data.decoded

        # extract message type
        msg_type = data['msg_type']

        # filter using message type
        if not msg_type in self.allowed_msg_types:
            return

        try:
            self.writers[msg_type].writerow(evb1000_data.decoded)
        except KeyError:
            
            # if the key does not exist the file has to be
            # created for the first time
            filename = self.create_file_name(msg_type, data['id'])
            
            # file is opened in append mode so that a newly
            # connected tag with the same id logs in the same file
            fd = open( filename + '.csv', 'a')
            self.files[msg_type] = fd

            # create a new writer
            writer = csv.DictWriter(fd, evb1000_data.msg_fields)
            self.writers[msg_type] = writer

            # write the header
            writer.writeheader()
            
            # now the new data can be written
            writer.writerow(evb1000_data.decoded)
            
    def close(self):
        """
        Close the file descriptor.
        """
        print('close')
        for key in self.files:
            self.files[key].close()
