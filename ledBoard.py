__author__ = 'Mark'


class Board:
    def __init__(self, id, column, row, serial_connection):
        self.id = id
        self.column = column
        self.row = row
        self.serial_connection = serial_connection

    def refresh_leds(self, led_values):
        output_bytearray = bytearray([self.id])
        output_bytearray += self.led_encoder(led_values)
        output_bytearray += bytearray([ord("!")])
        self.serial_connection.write(output_bytearray)

    @staticmethod
    def led_encoder(led_values):
        """
        Converts list of led brightness values to serial data
        arg: list of led values [R,G,B,R,G,B, ..... ] limited to 3 bits (values 0-7)
        ret: bytearray, whitch can be sent direcly with Serial.write()
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