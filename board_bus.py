__author__ = 'Mark'
import ledBoard
import threading
import logging
import time


class BoardBus(threading.Thread):
    def __init__(self, serial_connection, data, update_fps, sensor_fps):
        super().__init__()
        self.serial_connection = serial_connection
        self.data = data
        self.update_fps = update_fps
        self.sensor_fps = sensor_fps

        self._change_in_flags = threading.Event()  # something has changed (signal thread to continue)
        self._stop_flag = False  # event used to stop the thread
        self._update_flag = False  # update is pending
        self._read_sensors_flag = False  # reading sensors is pending

        self.boards = []  # list of boards connected to this bus
        self.broadcast_board = ledBoard.Board(ledBoard.BROADCAST_ADDRESS,
                                              self.serial_connection)  #all boards will listen if data is sent to this board

    def run(self):
        logging.info(self.serial_connection.name + " serial update thread started up")

        while not self._stop_flag:  # while stop signal is not given
            if self._change_in_flags.wait():  # Wait until something happens
                self._change_in_flags.clear()

                if self._update_flag:
                    self._update_flag = False  # TODO: TEST with this commented (possible bug seen wit one board)
                    self._refresh_boards()  # If given, update boards
                    self.update_fps.cycle_complete()

                if self._read_sensors_flag:
                    self._read_sensors_flag = False
                    self._read_sensors()
                    self.sensor_fps.cycle_complete()

        logging.info(self.serial_connection.name + " serial update thread stopped")
        self.turn_off_boards()

    def stop(self):
        self._change_in_flags.set()
        self._stop_flag = True

    def update(self):
        self._change_in_flags.set()
        self._update_flag = True

    def read_sensors(self):
        self._change_in_flags.set()
        self._read_sensors_flag = True

    def turn_off_boards(self):
        input_list = 100 * 3 * [0]
        #TODO: test if still needed
        for i in range(2): #Hack to ensure turning boards off in the end. Not really sure, why does it work.
            self.broadcast_board.refresh_leds(input_list)

    def _refresh_boards(self):
        for board in self.boards:
            numpy_input = self.data[board.row * 10:board.row * 10 + 10, board.column * 10:board.column * 10 + 10]
            input_list = self.numpy_to_input_list(numpy_input)
            board.refresh_leds(input_list)

    @staticmethod
    def numpy_to_input_list(np_list):
        input_list = []
        reverse = False
        for row in np_list:
            if reverse:
                row = (list(row[::-1]))
            else:
                row = (list(row))
            for color in row:
                for color_element in color:
                    input_list.append(color_element >> 5)
            reverse = not reverse
        return input_list

    def _read_sensors(self): #SLASH/GET BOARDS CURRENTLY CONNECTED
        self.broadcast_board.read_sensor()
        curr_serial = self.broadcast_board.serial_connection #TODO: chenge it to self.serial
        start = time.time()
        read_period = 0.010  # read answers for 10ms (should be enough for less than 20 boards)
        buffer = ""
        selected_board = None

        while time.time()-start < read_period:
            #TODO: Catch exceptions emerging from invalid data coming from serial
            #just inform and continue
            if curr_serial.inWaiting():
                received_char_code = curr_serial.read()[0]
                received_char = chr(received_char_code)

                #If board ID received
                if 128 <= received_char_code < 255:
                    buffer = ""
                    #Select new board:
                    for board in self.boards:
                        if board.id == received_char_code:
                            selected_board = board
                            break
                    else:   #We have found a board not currently known
                        logging.info("Board found:" + str(received_char_code))
                        #TODO: ASSIGN board with row and col
                        selected_board = ledBoard.Board(received_char_code, self.serial_connection)

                # This code marks the end of value
                elif received_char_code == 46:
                    selected_board.set_sensor_value(int(buffer))
                    selected_board = None
                elif '0' >= received_char <= '9':
                    buffer += received_char

                else:
                    #TODO: Catch it!
                    pass
                    #raise IOError("Invalid character received from serial")

        '''
        last_sensor_read = time.time()
        sensor_read_period = 0.25

        if time.time() - last_sensor_read >= sensor_read_period:
            last_sensor_read = time.time()
            self.read_sensors()
        '''
