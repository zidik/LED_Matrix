__author__ = 'Mark Laane'

import logging
import threading
import time

import serial
import numpy


# "Cairocffi" could be also installed as "cairo"
try:
    import cairocffi as cairo
except ImportError:
    import cairo

from board_bus import BoardBus
from fpsManager import FpsManager
from timer import Timer


class MatrixController:
    def __init__(self, serial_ports):
        self.serial_ports = serial_ports
        self.data_update_callback = None
        self.game = None
        # TODO - bug here if dims don't match
        self.surface_dims = 100, 100
        self.fps = dict(Game=FpsManager(), Sensor=FpsManager())
        self._stop = threading.Event()
        self.threads = []
        self.board_buses = []
        self.buttons = []
        # Cairo surface for drawing on
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.surface_dims[0], self.surface_dims[1])
        self.context = cairo.Context(self.surface)
        # Numpy array of data displayed on floor and GUI
        #Image from Cairo surface is copied into this buffer every frame
        self.displayed_data = numpy.zeros((self.surface_dims[0], self.surface_dims[1], 3), dtype=numpy.uint8)

        self.assign_boards()

        self.start()



    @staticmethod
    def assign_boards():
        for y in range(10):
            for x in range(10):
                BoardBus.add_assignation(128 + 10 * y + x, x, y)

    def start(self):
        self.board_buses = []
        self.threads = []

        for port in self.serial_ports:
            try:
                connection = serial.Serial(port=port, baudrate=500000, writeTimeout=0)
                new_bus = BoardBus(connection, self.displayed_data)
                self.board_buses.append(new_bus)
                self.threads.append(new_bus)
            except serial.SerialException:
                logging.exception("Unable to open serial port")

        # GameLoop - updates data for displaying
        t = threading.Thread(target=self.update_data, name="DataUpd Thread")
        self.threads.append(t)

        #"Sensor Refresh"-Loop - updates sensor readings
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
            bus.broadcast_board.ping()

    def stop(self):
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

    # noinspection PyTypeChecker
    def update_data(self):
        fps = 25
        update_period = 1.0/fps

        next_update = time.time()
        loopcount = 0

        while not self._stop.isSet() and fps != 0:
            results = 6 * [-1]
            with Timer() as t0:

                # Poll buttons -> this will call associated functions when buttons are pressed.
                for button in self.buttons:
                    assert isinstance(button, BoardButton)
                    button.poll()

                # # UPDATE
                if self.game is not None:

                    with Timer() as t1:
                        self.game.step()
                    results[1] = t1.milliseconds

                    start = time.time()
                    self.game.draw(self.context)
                    results[2] = (time.time()-start)*1000

                    with Timer() as t3:
                        # Get data from surface and convert it to numpy array
                        self.surface.flush()
                        buf = self.surface.get_data()
                        a = numpy.frombuffer(buf, numpy.uint8)
                        a.shape = (self.surface_dims[0], self.surface_dims[1], 4)
                        # Strip Alpha values and copy to our main numpy array
                        # also switch BGR to RGB
                        numpy.copyto(self.displayed_data[:, :, 0], a[:, :, 2])
                        numpy.copyto(self.displayed_data[:, :, 1], a[:, :, 1])
                        numpy.copyto(self.displayed_data[:, :, 2], a[:, :, 0])
                    results[3] = t3.milliseconds

                ##UPDATE END

                self.signal_update_boards()
                if self.data_update_callback is not None:
                    self.data_update_callback()  # signal caller (GUI for example)
                self.fps["Game"].cycle_complete()


                next_update += update_period
                sleep_time = next_update - time.time()

                skipped_frames = 0
                while sleep_time < 0:
                    with Timer() as t5:
                        #SKIP FRAMES!
                        if self.game is not None:
                            self.game.step()
                        next_update += update_period
                        sleep_time = next_update - time.time()
                        skipped_frames += 1
                    results[5] += t5.milliseconds
                else:
                    #Normal execution - sleep time is positive
                    with Timer() as t4:
                        self._stop.wait(sleep_time)
                    results[4] = t4.milliseconds


            results[0] = t0.milliseconds

            # Timing info
            loopcount += 1
            if loopcount > 10*fps or skipped_frames > 0:
                loopcount = 0
                logging.debug(
                    "update total: {0[0]:.3f} step: {0[1]:.3f}ms, "
                    "draw: {0[2]:.3f}ms, convert: {0[3]:.3f}ms, \n"
                    "sleep: {0[4]:.3f}ms({1:.3f}) skipped_frames: {2} - {0[5]:.3f}ms".format(
                        results,
                        sleep_time*1000,
                        skipped_frames
                    )
                )


        logging.debug("Thread \"{}\" stopped".format(threading.current_thread().name))

    def refresh_sensor_data(self):
        fps = 25
        next_update = time.time()

        while not self._stop.isSet() and fps != 0:
            for bus in self.board_buses:
                bus.read_sensors()

            next_update += 1.0 / fps
            sleep_time = next_update - time.time()
            if sleep_time > 0:
                self._stop.wait(sleep_time)

        logging.debug("Thread \"{}\" stopped".format(threading.current_thread().name))

    def signal_update_boards(self):
        for bus in self.board_buses:
            bus.refresh_leds()

    def add_button(self, board_id, function, args=None, override_key=None):
        self.buttons.append(
            BoardButton(board_id, self.board_buses, function, args, override_key)
        )

    def connect(self, event_name, update_gui):
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