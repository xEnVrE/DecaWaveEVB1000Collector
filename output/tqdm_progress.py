# tqdm progress information
from tqdm import tqdm

import sys

class TqdmProgress:
    """
    Tqdm progress meters that shows information about
    the total number of messages received from DecaWave EVB1000
    devices, their types and their rate.
    """
    def __init__(self, tqdm_position, tqdm_pos_lock):
        # empty dictionary of meters one for each message type
        self.meters = dict()

        # save reference to tqdm position index
        self.tqdm_position = tqdm_position
        self.tqdm_pos_lock = tqdm_pos_lock

    def create_description(self, msg_type, data):
        """
        Create meter description depending on the data received.
        """

        desc = ''

        # decide description depending on the message type
        if msg_type == 'arr':
            desc = '(autorng) anchor '
        elif msg_type == 'tpr':
            desc = '(trilat) tag '
        elif msg_type == 'trr':
            desc = '(ranging) tag '
        elif msg_type == 'apr':
            desc = '(anchor pos) tag '

        # add the device ID
        desc += str(data['id'])
            
        return desc

    def get_tqdm_position(self):
        """
        Obtain a position in the tqdm output list.
        """

        self.tqdm_pos_lock.acquire()
            
        pos = self.tqdm_position.value
        self.tqdm_position.value = pos + 1
            
        self.tqdm_pos_lock.release()

        return pos

    def free_tqdm_position(self):
        """
        Free the position in the tqdm output list.
        """
        self.tqdm_pos_lock.acquire()
            
        pos = self.tqdm_position.value
        self.tqdm_position.value = pos - 1
            
        self.tqdm_pos_lock.release()

    def new_message_event(self, evb1000_data):
        """
        Update the progress meter when a new message arrives.
        """
        # extract data
        data = evb1000_data.decoded

        # extract message type
        msg_type = data['msg_type']

        # get the meter depending on msg_type
        try:
            meter = self.meters[msg_type]
        except KeyError:

            # get the position of the progress meter
            pos = self.get_tqdm_position()
            
            # if the key does not exist the meter has to be created
            meter = tqdm(unit='msg', bar_format = '{desc}:{bar}{rate_fmt}', position = pos)
            self.meters[msg_type] = meter

            # set the description
            meter.desc = self.create_description(msg_type, data)

        finally:
            # in any case update and flush
            meter.update(1)
            sys.stdout.flush()
