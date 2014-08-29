__author__ = 'Mark'

from enum import Enum, unique
import logging

import numpy


BROADCAST_ADDRESS = 255


class Board:
    """
    This class describes all properties and functions of one LED board.
    """

    @unique
    class Command(Enum):
        """ All command-codes sent over serial """
        # From Board to Master
        request_id = 0x02
        pong = 0x05
        sensor_data = 0x12
        info = 0x1E
        debug = 0x1F

        # From Master to Board
        reset_id = 0x01
        offer_id = 0x03
        ping_from_master = 0x04
        offer_sequence_number = 0x06
        send_led_data = 0x10
        request_sensor = 0x11
        request_info = 0x1D

    command_codes = [command.value for command in Command]

    def __init__(self, board_id, serial_connection, column=None, row=None):
        self.id = board_id
        self.serial_connection = serial_connection
        self.column = column
        self.row = row
        self.sensor_value = -1
        self.data_currently_displayed = None

    # TODO: move some of those commands to BroadcastBoard
    def reset_id(self):
        """
        Resets board's ID to broadcast address.

        (This causes board to stop and wait for user to press it's pressure-sensor.
        Board will ask for new ID when user presses the sensor.)
        """
        self._send_command(Board.Command.reset_id, bytearray([ord('R'), ord('S'), ord('T')]))
        if self.id == BROADCAST_ADDRESS:
            logging.debug("Reset all board ID's on " + self.serial_connection.name)
        else:
            logging.debug("Reset board {} on {}".format(self.id, self.serial_connection.name))

    def assign_board_id(self, board_id):
        """
        Assigns board a new ID

        Args:
            board_id: new ID for board
        """
        self._send_command(Board.Command.offer_id, bytearray([board_id]))
        logging.debug("Assigned board id {}".format(board_id))

    def assign_sequence_number(self, sequence_number):
        """
        Assigns board a new sequence number

        Args:
            sequence_number: new sequence number for board
        """
        # Sequence is sent in values between 64 and 127 (these are not used for commands or id's
        #encoded_sequence_number = list()
        #while sequence_number > 0:
        #    encoded_sequence_number.append(sequence_number & 0b00111111)
        #    sequence_number >>= 6
        encoded_sequence_number = [(sequence_number & 0b00111111) + 64, ((sequence_number >> 6) & 0b00111111) + 64]

        self._send_command(Board.Command.offer_sequence_number, bytearray(encoded_sequence_number))
        logging.debug("Assigned board id={} sequence number {}".format(self.id, sequence_number))

    def ping(self):
        """
        Pings board - all boards on bus (with ID's) will answer in sequence (in order of their ID)
        """
        self._send_command(Board.Command.ping_from_master)
        if self.id == BROADCAST_ADDRESS:
            logging.debug("Pinging boards on " + self.serial_connection.name)
        else:
            logging.debug("Pinging board {} on {}".format(self.id, self.serial_connection.name))

    def refresh_leds(self, new_data):
        """
        Sends data to be displayed on board's LED's

        @param new_data: 10x10x3 slice of numpy array
        @return: boolean: whether update was needed
        """
        # ### FOR DEBUG ### #
        # If set to True, boards that are already displaying same data, will be skipped.
        # If set to False, boards will always refresh
        skip_boards = True
        # ################# #

        if skip_boards:
            if self.data_currently_displayed is None or (self.data_currently_displayed != new_data).any():
                self.data_currently_displayed = numpy.copy(new_data)
            else:
                return False

        encoded_data = self.led_encoder(new_data)
        self._send_command(Board.Command.send_led_data, encoded_data)
        return True

    def read_sensor(self):
        """
        Sends out command for board to answer with it's sensor value
        """
        self._send_command(Board.Command.request_sensor)

    def request_info(self):
        """
        Sends out command for board to answer with it's version string and other info
        """
        logging.debug("Requesting info from boards on " + self.serial_connection.name)
        self._send_command(Board.Command.request_info)

    def _send_command(self, command, data=None):
        """
        Sends command with board's ID and command code.
        Encloses command  with start and stop marks, so it is easy to filter echo.

        Args:
            command: command to send
            data: data to send with command
        """
        output = bytearray([ord("<")])

        output += bytearray([self.id])
        if data is not None:
            output += data
        assert isinstance(command, Board.Command)
        output += bytearray([command.value])

        output += bytearray([ord(">")])
        self.serial_connection.write(output)

    def set_sensor_value(self, value):
        """
        Sets sensor's value.
        Args:
            value: new sensor value
        Raises:
            ValueError: If value is outside ADC output boundaries.
        """
        if 0 <= value <= 1023:
            self.sensor_value = value
        else:
            raise ValueError("attempt to set sensor value to {}".format(value))

    def is_button_pressed(self):
        """
        Tests if pressure sensor is currently pressed.
        """
        if self.sensor_value > 100:
            return True
        else:
            return False

    @staticmethod
    def led_encoder(led_value_array):
        """
        @param led_value_array: numpy array of displayed image
        @return: bytes, which can be sent directly to serial.write()
        """
        # TODO: GET A VIEW?
        arr = numpy.copy(led_value_array)
        arr[1::2] = arr[1::2, ::-1]  # Reverse direction of every second row
        values = arr.ravel()  # Change to one long array
        values >>= 5
        # Sum every pair of elements (with second element rolled) and add required bit
        output_array = (values[::2] << 3) + values[1::2] + (1 << 6)
        return output_array.tostring()