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

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, state):
        self._enabled = state
        
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
        if msg_type != 'tpr' and msg_type != 'apr'\
        and msg_type != 'kmf':
            return 

        try:
            self.writers[msg_type].writerow(evb1000_data.decoded)
        except KeyError:
            
            # if the key does not exist the file has to be
            # created for the first time
            filename = "tag_" + str(data['tag_id']) + "_" +\
                       time.strftime("%d_%m_%Y") + "_" + str(msg_type)
            
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
