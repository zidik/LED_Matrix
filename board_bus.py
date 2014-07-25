__author__ = 'Mark Laane'
import threading
import logging
import time
import queue
import math

from ledBoard import Board, BROADCAST_ADDRESS
from fpsManager import FpsManager


class BoardBus(threading.Thread):
    """
    This class describes all properties and functions of one bus.
    Bus maintains all boards connected to it by one serial connection.
    Each bus has it's own thread.
    """

    board_assignment = []
    _id_pool = queue.Queue()

    @staticmethod
    def add_assignation(board_id, x, y):
        """
        Adds assignation to a list so bus knows what part of image data to send to board with specified ID. (when found)
        """
        BoardBus.board_assignment.append([board_id, x, y])
        BoardBus._id_pool.put_nowait(board_id)

    def __init__(self, serial_connection, data):
        super().__init__()
        self.serial_connection = serial_connection
        self.data = data

        self.fps = {
            "LED update": FpsManager(),
            "Sensor poll": FpsManager(),
            "Sensor response": FpsManager()
        }

        self.name = "{} Send".format(self.serial_connection.name)

        self._stop_flag = False  # event used to stop the threads
        self._update_display_flag = False  # update is pending (is currently in queue)
        self._read_sensors_flag = False  # reading sensors is pending (is currently in queue)

        self._command_queue = queue.Queue()  # Queue of functions - to be executed in BoardBus thread in order

        self.ignoring_serial_echo = False
        self.ignored_buffer = ""

        self.boards = []  # list of boards connected to this bus
        self.next_sequence_no = 0

        # All boards will listen if data is sent to this board
        self._broadcast_board = Board(BROADCAST_ADDRESS, self.serial_connection)

        self._responses = queue.Queue()
        self.current_response = {}

        self.silence_until = time.time()

        self.threads = []
        t = threading.Thread(target=self._run_receiving_thread, name="{} Receive".format(self.serial_connection.name))
        self.threads.append(t)
        t = threading.Thread(target=self._run_sending_thread, name="{} Send".format(self.serial_connection.name))
        self.threads.append(t)

        #FOR DEBUGGING:
        self.reset_id_all()

    def _run_receiving_thread(self):
        """
        This reads serial port byte-by-byte and puts received responses into self._responses
        Produced responses will be consumed in BoardBus thread
        """
        logging.debug(self.serial_connection.name + " serial Receive thread started")
        self.serial_connection.timeout = 0.1
        while not self._stop_flag:
            received_data = self.serial_connection.read()
            if len(received_data) == 0:
                continue
            else:
                received_char_code = received_data[0]
            received_char = chr(received_char_code)

            # Echo Ignoring
            if received_char == '<':
                self.ignoring_serial_echo = True
            if self.ignoring_serial_echo:
                self.ignored_buffer += received_char
                if received_char == '>':
                    self.ignoring_serial_echo = False
                    # logging.debug("Ignored data: \"{}\" ".format(self.ignored_buffer))
                    self.ignored_buffer = ""
                continue  # This is echo, let's read next byte

            # If board ID received
            if 128 <= received_char_code < 255:
                if self.current_response != {}:
                    logging.error("incomplete data from bus: {}".format(self.current_response))
                self.current_response = dict()
                self.current_response['id'] = received_char_code
            elif received_char_code in [command.value for command in Board.Command]:
                self.current_response['code'] = Board.Command(received_char_code)
                self._responses.put_nowait(self.current_response)
                self.current_response = {}
            else:
                try:
                    self.current_response['data'] += received_char
                except KeyError:
                    self.current_response['data'] = received_char
        logging.debug(self.serial_connection.name + " serial Receive thread stopped")

    def _run_sending_thread(self):
        """
        This thread sends commands over serial
        Thread waits for commands in queue and then sends them
        """

        logging.debug(self.serial_connection.name + " serial Sending thread started")
        while not self._stop_flag:
            try:
                command, args = self._command_queue.get(timeout=0.1)
            except queue.Empty:
                pass
            else:
                #Sleep until silence is over
                while self.silence_until > time.time():
                    time.sleep((self.silence_until - time.time()) % 0.1)  # sleep 100ms max
                command(*args)

        time.sleep(0.1) # wait for boards to start listening (finish their led refresh)

        #Sleep until silence is over
        while self.silence_until > time.time():
            time.sleep((self.silence_until - time.time()) % 0.1)  # sleep 100ms max
        self._turn_off_boards()
        logging.debug(self.serial_connection.name + " serial Sending thread stopped")

    def run(self):
        logging.debug(self.serial_connection.name + " serial Process thread started")
        self._stop_flag = False
        #Start SEND/RECEIVE threads
        for thread in self.threads:
            thread.start()

        while not self._stop_flag:
            try:
                response = self._responses.get(timeout=0.1)  # Check stop-flag every 100ms
            except queue.Empty:
                pass
            else:
                self._process_response(response)
        logging.debug(self.serial_connection.name + " serial Process thread stopped")

    def join(self, timeout=None):
        """
        Stop the thread and subthreads
        """
        self.stop()
        for thread in self.threads:
            thread.join()
        threading.Thread.join(self, timeout)

    def stop(self):
        """
        Signals thread to stop gracefully after finishing current loop cycle.
        """
        self._stop_flag = True

    def refresh_leds(self):
        """
        Signals thread to refresh image on boards next cycle. (if not already scheduled)
        """
        if not self._update_display_flag:
            self._update_display_flag = True
            self._command_queue.put_nowait((self._refresh_leds, []))

    def read_sensors(self):
        """
        Signals thread to poll sensors on boards next cycle. (if not already scheduled)
        """
        if not self._read_sensors_flag:
            self._read_sensors_flag = True
            self._command_queue.put_nowait((self._read_sensors, []))

    def turn_off_boards(self):
        """
        Signals thread to turn off boards next cycle
        """
        self._command_queue.put_nowait((self._turn_off_boards, []))

    def reset_id(self, board):
        """
        Signals thread to reset board ID next cycle
        """
        self._command_queue.put_nowait((self._reset_id, [board]))

    def reset_id_all(self):
        """
        Signals thread to reset all ID's next cycle
        """
        self._command_queue.put_nowait((self._reset_id, [self._broadcast_board]))

    def ping(self, board):
        """
        Signals thread to ping board next cycle
        """
        self._command_queue.put_nowait((self._ping, [board]))

    def ping_all(self):
        """
        Signals thread to ping all boards next cycle
        """
        self._command_queue.put_nowait((self._ping, [self._broadcast_board]))

    def assign_board_id(self):
        """
        Signals thread to assign an id next cycle
        """
        self._command_queue.put_nowait((self._assign_board_id, []))

    def assign_board_seq_no(self, value):
        """
        Signals thread to assign a sequence number next cycle
        """
        self._command_queue.put_nowait((self._assign_board_seq_no, [value]))


    def _new_board(self, board_id):
        board = None
        for assignment in BoardBus.board_assignment:
            if assignment[0] == board_id:
                board = Board(board_id, self.serial_connection, assignment[1], assignment[2])
                logging.info(
                    "Assigned board {id} col={col} row={row}".format(id=board_id, col=assignment[1], row=assignment[2]))
                self.boards.append(board)
                break
        else:
            logging.warning("Assignment for board {} not found".format(board_id))

        return board

    @staticmethod
    # TODO: MAY BE REMOVED?
    def _delayed_function_call(delay, function, args=None):
        time.sleep(delay)
        if args is None:
            function()
        else:
            function(*args)

    @staticmethod
    def _numpy_to_input_list(np_list):
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

    def _process_response(self, response):
        """
        Processes one response from queue
        Each response code is treated in it's own if clause
        """

        if response['code'] == Board.Command.request_id:
            self.assign_board_id()

        elif response['code'] == Board.Command.pong:
            for board in self.boards:
                if board.id == response["id"]:
                    logging.debug("Board {} is already enumerated.".format(response["id"]))
                    break
            else:  # We have found a board not currently known
                logging.info("Board found: id={id}".format(**response))
                new_board = self._new_board(response["id"])
                self.assign_board_seq_no(new_board)

        elif response['code'] == Board.Command.sensor_data:
            try:
                _ = response["id"]
                _ = response["data"]
            except KeyError:
                logging.error("Received sensor data without id or data. \"{}\". ".format(response))
            else:
                self.fps["Sensor response"].cycle_complete()
                for board in self.boards:
                    if board.id == response["id"]:
                        try:
                            board.set_sensor_value(int(response["data"]))
                        except ValueError:
                            logging.exception("Setting sensor value failed. response=".format(response))
                        break
                else:
                    logging.error("Received sensor data from unknown board. \"{}\".".format(response))

        elif response['code'] == Board.Command.debug:
            try:
                logging.debug("Board debug: ID={id} Data=\"{data}\"".format(**response))
            except KeyError:
                logging.error("debug response didn't have ID or Data. response={}".format(response))

        else:
            logging.error("UNKNOWN RESPONSE CODE. Response={}".format(response))

    def _be_silent_next_us(self, us):
        self.silence_until = max(self.silence_until, time.time() + (us / 1000) / 1000)

    #
    # Methods below this line send data to serial bus:
    # They must ONLY be called from BoardBus thread.
    # BoardBus thread controls the timing and sequencing of these methods
    # Each of these methods have "safe" version above this line
    ###########################################################

    def _turn_off_boards(self):
        """
        Turns off all LED's on all boards on the bus
        """
        input_list = 100 * 3 * [0]
        # TODO: test if still needed
        for i in range(2):  # Hack to ensure turning boards off in the end. Not really sure, why does it work.
            self._broadcast_board.refresh_leds(input_list)

    @staticmethod
    def _reset_id(board):
        board.reset_id()

    def _ping(self, board):
        board.ping()
        slot_time = 300  # Time for each board in microseconds #TODO: ADJUST THIS
        #TODO: Reduce this
        additional_time = slot_time*0.05  # for clock diff
        number_of_boards = len(BoardBus.board_assignment)
        self._be_silent_next_us(number_of_boards * (slot_time + additional_time))

    def _refresh_leds(self):
        for board in self.boards:
            numpy_input = self.data[board.row * 10:board.row * 10 + 10, board.column * 10:board.column * 10 + 10]
            input_list = self._numpy_to_input_list(numpy_input)
            board.refresh_leds(input_list)
        self.fps["LED update"].cycle_complete()
        # TODO: TEST with next line commented (possible bug seen with one board)
        self._update_display_flag = False

    def _read_sensors(self):
        """
        NB! sensor readings are being buffered in hardware(Bus converter)
        this causes some of data to be read out next cycle
        """
        time.sleep(0.01)  # TODO: This has to be as long as one board sleeping
        self._broadcast_board.read_sensor()
        number_of_boards = self.next_sequence_no
        slot_time = 400  # Time for each board in microseconds #TODO: ADJUST THIS
        #TODO: Reduce this
        additional_time = slot_time*0.05  # for clock diff
        adc_time = 100  # time for waiting all boards to take adc measurement
        self._be_silent_next_us(number_of_boards * (slot_time + additional_time) + adc_time)
        self.fps["Sensor poll"].cycle_complete()
        self._read_sensors_flag = False

    def _assign_board_id(self):
        try:
            board_id = BoardBus._id_pool.get_nowait()
        except queue.Empty:
            logging.error("Unable to assign ID to board: There are more boards than assignations.")
        else:
            self._broadcast_board.assign_board_id(board_id)
            #Re enumerate after a delay
            time.sleep(0.1)    # TODO: Adjust this
            self._ping(self._broadcast_board) # TODO: Maybe ping only one

    def _assign_board_seq_no(self, board):
        board.assign_sequence_number(self.next_sequence_no)
        self.next_sequence_no += 1
