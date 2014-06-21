__author__ = 'Mark'
import threading
import logging
import time
import queue

from ledBoard import Board, BROADCAST_ADDRESS


class BoardBus(threading.Thread):
    _board_assignment = []
    _id_pool = queue.Queue()

    @staticmethod
    def add_assignation(board_id, x, y):
        BoardBus._board_assignment.append([board_id, x, y])
        BoardBus._id_pool.put_nowait(board_id)


    def __init__(self, serial_connection, data, update_fps, sensor_fps):
        super().__init__()
        self.serial_connection = serial_connection
        self.data = data
        self.update_fps = update_fps
        self.sensor_fps = sensor_fps

        self._change_in_flags = threading.Event()  # something has changed (signal thread to continue)
        self._stop_flag = False  # event used to stop the thread
        self._update_display_flag = False  # update is pending
        self._update_sensors_flag = False  # reading sensors is pending

        self.ignoring_serial_echo = False
        self.ignored_buffer = ""

        self.boards = []  # list of boards connected to this bus
        self.next_sequence_no = 0

        # All boards will listen if data is sent to this board
        self.broadcast_board = Board(BROADCAST_ADDRESS, self.serial_connection)

        self.responses = []
        self.current_response = {}

        self.silence_until = time.time()


    def run(self):
        logging.info(self.serial_connection.name + " serial update thread started up")

        while not self._stop_flag:  # while stop signal is not given
            # #### RECEIVING PART #####
            self._receive_data_from_bus()
            self._process_responses()

            # if computer waits for data from board, don't let it send
            if self.silence_until > time.time():
                continue

            # ##### SENDING PART  #####
            if self._change_in_flags.wait():  # Wait until something happens
                self._change_in_flags.clear()

                if self._update_display_flag:
                    self._update_display_flag = False  # TODO: TEST with this commented (possible bug seen wit one board)
                    self._refresh_boards()  # If given, update boards
                    self.update_fps.cycle_complete()

                if self._update_sensors_flag:
                    self._update_sensors_flag = False
                    self._read_sensors()
                    self.sensor_fps.cycle_complete()

        logging.info(self.serial_connection.name + " serial update thread stopped")
        self.turn_off_boards()

    def stop(self):
        self._stop_flag = True
        self._change_in_flags.set()

    def update(self):
        self._update_display_flag = True
        self._change_in_flags.set()

    def read_sensors(self):
        self._update_sensors_flag = True
        self._change_in_flags.set()

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

    def _read_sensors(self):
        """
        NB! sensor readings are being buffered in hardware(Bus converter)
        this causes some of data to be read out next cycle
        """
        self.broadcast_board.read_sensor()
        self.silence_until = time.time() + 0.01  # read answers for 10ms (should be enough for less than 20 boards)

    def _receive_data_from_bus(self):
        while self.serial_connection.inWaiting():
            received_char_code = self.serial_connection.read()[0]
            received_char = chr(received_char_code)

            # Echo Ignoring
            if received_char == '<':
                self.ignoring_serial_echo = True
            if self.ignoring_serial_echo:
                self.ignored_buffer += received_char
                if received_char == '>':
                    self.ignoring_serial_echo = False
                    logging.debug("Ignored data: \"{}\" ".format(self.ignored_buffer))
                    self.ignored_buffer = ""
                continue  # This is echo, let's read next byte

            # If board ID received
            if 128 <= received_char_code < 255:
                self.current_response['id'] = received_char_code
            elif received_char_code in [command.value for command in Board.Command]:
                self.current_response['code'] = Board.Command(received_char_code)
                self.responses.append(self.current_response)
                self.current_response = {}
            else:
                try:
                    self.current_response['data'] += received_char
                except KeyError:
                    self.current_response['data'] = received_char

    def _process_responses(self):
        while len(self.responses) > 0:
            response = self.responses.pop(0)

            if response['code'] == Board.Command.request_id:
                self.assign_board_id()

            elif response['code'] == Board.Command.pong:
                for board in self.boards:
                    if board.id == response["id"]:
                        logging.warning("This board is already enumerated.")
                else:  # We have found a board not currently known
                    logging.info("Board found: id={id}".format(**response))
                    self.assign_board_seq_no(self.new_board(response["id"]))

            elif response['code'] == Board.Command.sensor_data:
                print(response)
                for board in self.boards:
                    if board.id == response["id"]:
                        try:
                            board.set_sensor_value(int(response["data"]))
                        except ValueError:
                            logging.exception("Setting sensor value failed. response=".format(response))
                        break
                else:
                    logging.error("Received sensor data from unknown board. id={id} data=\"{data}\"".format(**response))

            elif response['code'] == Board.Command.debug:
                try:
                    print("Board debug: ID={id} Data=\"{data}\"".format(**response))
                except KeyError:
                    logging.exception("debug response didn't have ID or Data. response={}".format(response))

            else:
                logging.error("UNKNOWN RESPONSE CODE. Response={}".format(response))

    def assign_board_id(self):
        try:
            board_id = BoardBus._id_pool.get_nowait()
        except queue.Empty:
            logging.error("Unable to assign ID to board: There are more boards than assignations.")
            return
        self.broadcast_board.offer_board_id(board_id)
        # TODO: Reenumerate after a delay
        self.broadcast_board.enumerate()

    def assign_board_seq_no(self, board):
        board.offer_sequence_number(self.next_sequence_no)
        self.next_sequence_no += 1



    def new_board(self, board_id):
        board = None
        for assignment in BoardBus._board_assignment:
            if assignment[0] == board_id:
                board = Board(board_id, self.serial_connection, assignment[1], assignment[2])
                logging.info(
                    "Assigned board {id} col={col} row={row}".format(id=board_id, col=assignment[1], row=assignment[2]))
                self.boards.append(board)
                break
        else:
            logging.warning("Assignment for board {} not found".format(board_id))

        return board
