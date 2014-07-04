__author__ = 'Mark'

from enum import Enum
import logging

BROADCAST_ADDRESS = 255


class Board:
    """
    This class describes all properties and functions of one LED board.
    """

    class Command(Enum):
        """ All command-codes sent over serial """
        # From Board to Master
        request_id = 0x02
        pong = 0x05
        sensor_data = 0x12
        debug = 0x1F

        # From Master to Board
        reset_id = 0x01
        offer_id = 0x03
        ping_from_master = 0x04
        offer_sequence_number = 0x06
        send_led_data = 0x10
        request_sensor = 0x11

    def __init__(self, board_id, serial_connection, column=None, row=None):
        self.id = board_id
        self.serial_connection = serial_connection
        self.column = column
        self.row = row
        self.sensor_value = -1

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
        self._send_command(Board.Command.offer_sequence_number, bytearray([sequence_number]))
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

    def refresh_leds(self, led_values):
        """
        Sends data to be displayed on board's LED's
        Args:
            led_values: list of LED values
        """
        self._send_command(Board.Command.send_led_data, self.led_encoder(led_values))

    def read_sensor(self):
        """
        Sends out command for board to answer with it's sensor value
        """
        self._send_command(Board.Command.request_sensor)

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
    def led_encoder(led_values):
        """
        Converts list of led brightness values to serial data
        arg: list of led values [R,G,B,R,G,B, ..... ] limited to 3 bits (values 0-7)
        ret: bytearray, which can be sent directly with Serial.write()
        """
        output_byte = 0
        output = []
        byte_side = 1
        for i in range(len(led_values)):
            value = led_values[i]
            value &= 0b00000111  # Limit input TODO:Warn before limiting
            if byte_side == 1:
                output_byte = 0b01000000
                output_byte += (value << 3)
                byte_side = 2
                if i == len(led_values) - 1:
                    output.append(output_byte)
            else:
                output_byte += value
                byte_side = 1
                output.append(output_byte)
        return bytearray(output)