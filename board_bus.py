__author__ = 'Mark'
import threading
import logging
import time

import ledBoard


class BoardBus(threading.Thread):
    board_assignment = []

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

        # Variables for reading sensors:
        self.selected_board = None  # board currently being read (Id received, waiting for data))
        self.read_buffer = ""

        self.boards = []  # list of boards connected to this bus

        #All boards will listen if data is sent to this board
        self.broadcast_board = ledBoard.Board(ledBoard.BROADCAST_ADDRESS, self.serial_connection)

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
        # TODO: test if still needed
        for i in range(2):  # Hack to ensure turning boards off in the end. Not really sure, why does it work.
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
            for cell in row:
                for color_element in cell:
                    input_list.append(color_element >> 5)
            reverse = not reverse
        return input_list

    def _read_sensors(self):  # SLASH/GET BOARDS CURRENTLY CONNECTED
        """
        NB! sensor readings are being buffered in hardware(Bus converter)
        this causes some of data to be read next cycle
        """
        self.broadcast_board.read_sensor()
        start = time.time()
        read_period = 0.010  # read answers for 10ms (should be enough for less than 20 boards)

        while time.time() - start < read_period:
            # TODO: Catch exceptions emerging from invalid data coming from serial
            #just inform and continue
            if self.serial_connection.inWaiting():
                received_char_code = self.serial_connection.read()[0]
                received_char = chr(received_char_code)

                #If board ID received
                if 128 <= received_char_code < 255:
                    self.read_buffer = ""
                    #Select new board:
                    for board in self.boards:
                        if board.id == received_char_code:
                            self.selected_board = board
                            break
                    else:  # We have found a board not currently known
                        logging.info("Board found:" + str(received_char_code))
                        self.selected_board = self.new_board(received_char_code)

                # This code marks the end of value
                elif received_char_code == 46:
                    if self.selected_board is not None:
                        try:
                            self.selected_board.set_sensor_value(int(self.read_buffer))
                        except Exception:
                            logging.debug("setting sensor failed: buffer='" + str(self.read_buffer) +
                                          "' selected board=" + str(self.selected_board.id) + "'")
                        self.selected_board = None
                    else:
                        logging.debug("No board selected. buffer='" + str(self.read_buffer) + "'")
                elif '0' <= received_char <= '9':
                    self.read_buffer += received_char
                elif received_char_code == 0:
                    pass  # TODO:Test:DUNNO WHY RANDOM ZEROES ON BUS?
                else:
                    logging.debug("Invalid character received from serial. ascii_nr " + str(received_char_code)
                                  + " character:" + str(received_char))
                    #raise IOError("Invalid character received from serial")

    def new_board(self, board_id):
        board = None
        for assignment in BoardBus.board_assignment:
            if assignment[0] == board_id:
                board = ledBoard.Board(board_id, self.serial_connection, assignment[1], assignment[2])
                logging.info("Assigned board " + str(board_id) +
                             " col=" + str(assignment[1]) +
                             " row=" + str(assignment[2]))
                self.boards.append(board)
                break
        else:
            logging.warning("Assignment for board " + str(board_id) + " not found")

        return board
