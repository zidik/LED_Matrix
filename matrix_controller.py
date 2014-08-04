__author__ = 'Mark Laane'

import logging
import threading
import time

import serial
import numpy
import cairocffi as cairo

from board_bus import BoardBus
from fpsManager import FpsManager
from timer import Timer


class MatrixController:
    data_update_FPS = 25
    sensor_update_FPS = 25
    serial_ports = []  # List of serial port identifiers

    dimensions = 10, 10  # Number of boards in X and Y axis

    def __init__(self):
        self.data_update_callback = None
        self.game = None
        # TODO - bug here if dims don't match
        self.surface_dims = MatrixController.dimensions[0] * 10, MatrixController.dimensions[1] * 10
        self.fps = dict(Game=FpsManager(), Sensor=FpsManager())
        self._stop = threading.Event()
        self.threads = []
        self.board_buses = []
        self.buttons = []
        # Cairo surface for drawing on
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.surface_dims[0], self.surface_dims[1])
        self.context = cairo.Context(self.surface)
        # Numpy array of data displayed on floor and GUI
        # Image from Cairo surface is copied into this buffer every frame
        self.displayed_data = numpy.zeros((self.surface_dims[1], self.surface_dims[0], 3), dtype=numpy.uint8)

        self._assign_boards()

        self.start()

    @staticmethod
    def _assign_boards():
        for y in range(MatrixController.dimensions[1]):
            for x in range(MatrixController.dimensions[0]):
                BoardBus.add_assignation(128 + MatrixController.dimensions[0] * y + x, x, y)

    def start(self):
        """
        Connects to serial ports, creates BoardBus for each port and starts it's thread
        Creates and starts Data Update thread - runs the game loop
        Creates and starts Sensor Refrsh thread - polls sensors for valies
        Finally pings all boards on all buses for enumeration
        """
        self.board_buses = []
        self.threads = []

        for port in MatrixController.serial_ports:
            try:
                connection = serial.Serial(port=port, baudrate=500000, writeTimeout=0)
                new_bus = BoardBus(connection, self.displayed_data)
                self.board_buses.append(new_bus)
                self.threads.append(new_bus)
            except serial.SerialException:
                logging.exception("Unable to open serial port")

        # Data Update (Game Loop) - updates data for displaying
        t = threading.Thread(target=self.update_data, name="DataUpd Thread")
        self.threads.append(t)

        # "Sensor Refresh"-Loop - updates sensor readings
        t = threading.Thread(target=self.refresh_sensor_data, name="Sensor Thread")
        self.threads.append(t)

        logging.debug("Starting matrix controller threads")
        self._stop.clear()
        for thread in self.threads:
            thread.start()
        logging.debug("Matrix controller threads started")

        # Enumerate/ping boards
        for bus in self.board_buses:
            assert isinstance(bus, BoardBus)
            bus.ping_all()

    def stop(self):
        """
        Stops all child-threads
        Closes serial ports
        """
        logging.debug("Signalling matrix controller threads to stop")
        self._stop.set()
        for thread in self.threads:
            thread.join()
        logging.debug("Matrix controller stopped")

        logging.debug("Closing serial ports")
        for bus in self.board_buses:
            assert isinstance(bus, BoardBus)
            connection = bus.serial_connection
            assert isinstance(connection, serial.Serial)
            connection.close()
        logging.debug("Serial ports closed")

    def update_data(self):
        """
        Loop that advances the game/animation
        """
        fps = MatrixController.data_update_FPS
        if fps == 0:
            return
        update_period = 1.0 / fps

        next_update = time.time()

        while not self._stop.isSet() and fps != 0:

            # Poll buttons -> this will call associated functions when buttons are pressed.
            for button in self.buttons:
                assert isinstance(button, BoardButton)
                try:
                    button.poll()
                except ValueError as e:
                    logging.warning("{}".format(e))

            # # UPDATE
            if self.game is not None:

                self.game.step()
                self.game.draw(self.context)

                # Get data from surface and convert it to numpy array
                self.surface.flush()
                buf = self.surface.get_data()
                a = numpy.frombuffer(buf, numpy.uint8)
                a.shape = (self.surface_dims[1], self.surface_dims[0], 4)
                # Strip Alpha values and copy to our main numpy array
                # also switch BGR to RGB
                numpy.copyto(self.displayed_data[:, :, 0], a[:, :, 2])
                numpy.copyto(self.displayed_data[:, :, 1], a[:, :, 1])
                numpy.copyto(self.displayed_data[:, :, 2], a[:, :, 0])

            # #UPDATE END

            self._signal_update_boards()
            if self.data_update_callback is not None:
                # noinspection PyCallingNonCallable
                self.data_update_callback()  # signal caller (GUI for example)
            self.fps["Game"].cycle_complete()

            next_update += update_period
            sleep_time = next_update - time.time()

            skipped_frames = 0
            while sleep_time < 0:
                # SKIP FRAMES!
                if self.game is not None:
                    self.game.step()
                next_update += update_period
                sleep_time = next_update - time.time()
                skipped_frames += 1
            else:
                # Normal execution - sleep time is positive
                self._stop.wait(sleep_time)

            if skipped_frames > 0:
                logging.debug("skipped_frames: {}".format(skipped_frames))

        logging.debug("Thread \"{}\" stopped".format(threading.current_thread().name))

    def refresh_sensor_data(self):
        """
        Loop that polls sensor data from boards
        """
        fps = MatrixController.sensor_update_FPS
        update_period = 1.0 / fps
        next_update = time.time()

        while not self._stop.isSet() and fps != 0:
            for bus in self.board_buses:
                bus.read_sensors()

            next_update += update_period
            sleep_time = next_update - time.time()
            if sleep_time > 0:
                self._stop.wait(sleep_time)

        logging.debug("Thread \"{}\" stopped".format(threading.current_thread().name))

    def reset_id_all(self):
        for bus in self.board_buses:
            bus.reset_id_all()

    def _signal_update_boards(self):
        """
        Signals all buses to refresh data displayed on boards
        """
        for bus in self.board_buses:
            bus.refresh_leds()

    def add_button(self, board_id, function, args=None, override_key=None):
        self.buttons.append(
            BoardButton(board_id, self.board_buses, function, args, override_key)
        )

    def connect(self, event_name, update_gui):
        """
        connect function to an event.
        """
        # If data gets updated, data_update_callback will be called
        if event_name == "data_update":
            self.data_update_callback = update_gui


class BoardButton:
    """
        Tries to find correct board and then returns it's button's state
    """

    def __init__(self, board_id, board_buses, function, args=None, override_key=None):
        self.board_id = board_id
        self.board_buses = board_buses
        self.function = function
        self.args = args
        self.override_key = override_key

        self.overridden = False  # Is button currently overridden?
        self.board = None
        self.warning_timer = time.time()

    def is_pressed(self):
        if self.board is None:
            for bus in self.board_buses:
                for board in bus.boards:
                    if board.id == self.board_id:
                        self.board = board
        # Still not found after searching
        if self.board is None:
            # If no buttons found after 1 second: Warn user
            if self.warning_timer is not None and time.time() - self.warning_timer > 1.0:
                logging.warning("BoardButton {} not found".format(self.board_id))
                self.warning_timer = None
            return False
        return self.board.is_button_pressed()

    def is_overridden(self):
        return self.overridden

    def set_override(self, value):
        self.overridden = value

    def poll(self):
        if self.is_pressed() or self.is_overridden():
            if self.args is not None:
                self.function(*self.args)
            else:
                self.function()