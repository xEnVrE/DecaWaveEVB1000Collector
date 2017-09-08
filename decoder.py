import struct

def decode_unsigned_int(string):
    """
    Return the unsigned int coded in the hex string.
    """
    return int(string,16)

def decode_float(string):
    """
    Return the float coded in the hex string.
    """
    hex_code = bytes.fromhex(string)
    unpacked = struct.unpack('>f', hex_code)
    return unpacked[0]

def decode_string(string):
    """
    Return the string as is.
    """
    return string

def select_decoder(type_name):
    """
    Return a different decoder depending on type_name.
    """
    if type_name == 'u':
        return decode_unsigned_int
    elif type_name == 'f':
        return decode_float
    elif type_name == 's':
        return decode_string

class DataFromEVB1000:
    """
    Decodes a line coming from the EVB1000 serial.
    """

    def __init__(self, line):
        
        # remove trailing '\r\n' from the line
        self.line = line[:-2]

        # convert to string
        self.line = self.line.decode('utf-8')

        # empty msg_type
        self.msg_type = ''

        # empty msg_fields
        self._msg_fields = []

        # tries to decode message type and message
        self.msg_type_decoded = self.decode_msg_type()
        if (self.msg_type_decoded):
            self.decode()

    @property
    def msg_fields(self):
        return self._msg_fields

    @msg_fields.setter
    def msg_fields(self, fields):
        self._msg_fields = fields

    @property
    def decoded(self):
        return self._decoded

    def decode_msg_type(self):
        """
        Determine the type of the message.

        Types implemented are

        tag_position_report   := msg_type = 'tpr', tag_id,  
                                 (string),         (unsigned),    

                                 pos_x,      pos_y,     pos_z
                                 (float),    (float),   (float)

        anch_positions_report := mst_type = 'apr', tag_id
                                 (string),         (unsigned),    

                                 pos_x_a0,   pos_y_a0,   pos_z_a0
                                 (float),    (float),    (float)

                                 pos_x_a1,   pos_y_a1,   pos_z_a1
                                 (float),    (float),    (float)

                                 pos_x_a2,   pos_y_a2,   pos_z_a2
                                 (float),    (float),    (float)

                                 pos_x_a3,   pos_y_a3,   pos_z_a3
                                 (float),    (float),    (float)

        If the type is valid the field names of the message 
        and its structure are stored and the function return True.

        Otherwise return False.
        """

        # msg_type is always 3 characters long
        if len(self.line) < 3:
            return False

        # get msg_type
        msg_type = self.line[0:3]

        # set field names and structure depending on the msg_type
        if msg_type == 'tpr':
            self.msg_fields = ['msg_type', 'tag_id', 'x', 'y', 'z']
            self.msg_structure = ['s'] + ['u'] + ['f'] * 3
        elif msg_type == 'apr':
            self.msg_fields = ['msg_type', 'tag_id',\
                               'a0_x', 'a0_y', 'a0_z',
                               'a1_x', 'a1_y', 'a1_z',
                               'a2_x', 'a2_y', 'a2_z',
                               'a3_x', 'a3_y', 'a3_z']
            self.msg_structure = ['s'] + ['u'] + ['f'] * 12
        else:
            return False

        return True

    def decode(self):
        """
        Return a dictionary containing the fields
        decoded from the message line.
        """

        # make a list of items from the line string
        items = self.line.split(' ')

        # empty list of decoded values
        decoded = []
        
        for index, item in enumerate(items):
            # extract type for the current item
            item_type_name = self.msg_structure[index]

            # pick the right decoder
            decoder = select_decoder(item_type_name)
            decoded.append(decoder(item))

        # return a dictionary
        self._decoded =  dict(zip(self.msg_fields, decoded))

if __name__ == '__main__':
    # some testing
    # tag position report with tag_id = 2, x = y = z = 10.34
    example_line = 'tpr 02 412570a4 412570a4 412570a4\r\n'

    # instantiate obj
    d = DataFromEVB1000(example_line)

    if (d.decode_msg_type()):
        print(d.decode())
    
