__author__ = 'Mark'

import logging

BROADCAST_ADDRESS = 255


class Board:
    def __init__(self, board_id, serial_connection, column=None, row=None):
        self.id = board_id
        self.serial_connection = serial_connection
        self.column = column
        self.row = row
        self.sensor_value = -1

    def refresh_leds(self, led_values):
        output = bytearray([self.id])
        output += self.led_encoder(led_values)
        output += bytearray([ord("!")])
        self.write_to_serial(output)

    def read_sensor(self):
        """ Sends out command for board to answer with it's sensor value"""
        output = bytearray([self.id])
        output += bytearray([ord("?")])
        self.write_to_serial(output)

    def write_to_serial(self, data):
        output = bytearray([ord("<")])
        output += data
        output += bytearray([ord(">")])
        self.serial_connection.write(output)

    def set_sensor_value(self, value):
        if 0 <= value <= 1023:
            self.sensor_value = value
        else:
            logging.debug("attempt to set sensor value to {}".format(value))

    def is_button_pressed(self):
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