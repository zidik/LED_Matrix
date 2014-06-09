__author__ = 'Mark'

import tkinter
import logging
import threading
import time

import serial
import PIL.Image
import PIL.ImageTk
import numpy
import cairo
from enum import Enum

import fpsManager
import board_bus
import pong
import breaker
import test_pattern


class App(object):
    class Mode(Enum):
        test = 0
        pong = 1
        breaker = 2

    def __init__(self, master, serial_ports):

        """
        board_bus.BoardBus.board_assignment = [
            [128, 0, 0],
            [129, 1, 0],
            [130, 0, 1],
            [131, 1, 1]
        ]
        """

        board_bus.BoardBus.board_assignment = []
        for i in range(10):
            for j in range(10):
                board_bus.BoardBus.board_assignment.append([128 + 10 * i + j, j, i])

        self.canvas_dims = 300, 300

        self.mode = App.Mode.breaker

        master.bind_all('<Escape>', lambda event: event.widget.quit())
        self.master = master
        self.frame = tkinter.Frame(self.master, width=600, height=400)
        self.frame.pack()  # (fill=tkinter.BOTH, expand=1) TODO?
        self.canvas = tkinter.Canvas(self.frame, width=self.canvas_dims[0], height=self.canvas_dims[1])
        self.canvas.pack()

        self.buttons = []
        self.frame.bind("<Key>", self.key_press)
        self.frame.bind("<KeyRelease>", self.key_release)
        self.frame.focus_set()

        self.photo = None  # Holds TkInter image for displaying in GUI

        #TODO - bug here if dims don't match
        self.surface_dims = 100, 100

        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.surface_dims[0], self.surface_dims[1])
        self.context = cairo.Context(self.surface)

        self.data = numpy.zeros((self.surface_dims[0], self.surface_dims[1], 3), dtype=numpy.uint8)

        serial_connections = []
        for port in serial_ports:
            try:
                serial_connections.append(serial.Serial(port=port, baudrate=500000))
            except serial.SerialException as e:
                logging.warning("Unable to open serial port")
                logging.exception(e)

        #List of fps objects about app (which need periodical refreshing)
        self.app_fps_list = []

        #GUI FPS
        gui_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=gui_fps_var).pack()
        self.gui_fps = fpsManager.FpsManager(string_var=gui_fps_var, string_var_text="GUI: {} FPS", update_period=0.5)
        self.app_fps_list.append(self.gui_fps)

        # Create all buses
        self.board_buses = []

        for connection in serial_connections:
            update_fps_var = tkinter.StringVar()
            tkinter.Label(self.frame, textvariable=update_fps_var).pack()
            update_fps = fpsManager.FpsManager(
                string_var=update_fps_var,
                string_var_text=str(connection.name) + " update: {} FPS"
            )
            self.app_fps_list.append(update_fps)

            sensor_fps_var = tkinter.StringVar()
            tkinter.Label(self.frame, textvariable=sensor_fps_var).pack()
            sensor_fps = fpsManager.FpsManager(
                string_var=sensor_fps_var,
                string_var_text=str(connection.name) + " sensor: {} FPS"
            )
            self.app_fps_list.append(sensor_fps)

            new_bus = board_bus.BoardBus(connection, self.data, update_fps, sensor_fps)
            self.board_buses.append(new_bus)

        #Sensor value display
        self.sensor_gui_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=self.sensor_gui_var).pack()

        self.update_flags = {}
        self.signal_update_gui_and_boards()

        self._stop = threading.Event()
        self.threads = []

        # GameLoop - updates data for displaying
        t = threading.Thread(target=self.update_data)
        self.threads.append(t)

        #"Sensor Refresh"-Loop - updates sensor readings
        t = threading.Thread(target=self.refresh_sensor_data)
        self.threads.append(t)

        #Start all threads
        for thread in self.threads:
            thread.start()

        #Start bus threads
        for bus in self.board_buses:
            bus.start()

        #Start refreshing GUI
        self.master.after(0, self._refresh_gui)

    def stop(self):
        self._stop.set()
        logging.debug("Waiting for app threads to stop")
        for thread in self.threads:
            thread.join()
        logging.debug("Threads stopped, Stopping board buses")
        for bus in self.board_buses:
            bus.stop()
        logging.debug("Waiting for bus threads to stop")
        for bus in self.board_buses:
            if bus.isAlive():
                bus.join()
        logging.debug("App stopped")

    def _refresh_gui(self):
        fps = 50
        next_update = time.time()

        ## UPDATE
        if self.update_flags['GUI']:
            self.update_flags['GUI'] = False
            im = PIL.Image.fromarray(self.data)
            im = im.resize((self.canvas_dims[0], self.canvas_dims[1]))
            self.photo = PIL.ImageTk.PhotoImage(image=im)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)

            self.gui_fps.cycle_complete()

            #Update FPS
            for fps_manager in self.app_fps_list:
                fps_manager.update_string_var()
        ##UPDATE END

        temp_gui_string = ""
        for bus in self.board_buses:
            for board in bus.boards:
                temp_gui_string += str(board.sensor_value) + "\n"
        self.sensor_gui_var.set(temp_gui_string)

        next_update += 1.0 / fps
        sleep_time = round((next_update - time.time())*1000)
        if sleep_time <= 0:
            sleep_time = 1

        if not self._stop.isSet():
            self.master.after(sleep_time, self._refresh_gui)

    def update_data(self):
        fps = 40

        #Game FPS
        game_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=game_fps_var).pack()
        game_fps = fpsManager.FpsManager(string_var=game_fps_var, string_var_text="Game: {} FPS")
        self.app_fps_list.append(game_fps)

        next_update = time.time()

        game = None
        if self.mode == App.Mode.pong:
            game = pong.Pong(self.surface_dims)
            self.assign_pong_keys_to_boardbuttons(game)
        elif self.mode == App.Mode.test:
            game = test_pattern.TestPattern(self.surface_dims, board_bus.BoardBus.board_assignment, self.board_buses)
        elif self.mode == App.Mode.breaker:
            game = breaker.Breaker(self.surface_dims)
            self.assign_breaker_keys_to_boardbuttons(game)

        while not self._stop.isSet() and fps != 0:

            #Poll buttons -> this will call associated functions when buttons are pressed.
            for button in self.buttons:
                assert isinstance(button, BoardButton)
                button.poll()

            ## UPDATE
            game.step()
            game.draw(self.context)

            # Get data from surface and convert it to numpy array
            buf = self.surface.get_data()
            a = numpy.frombuffer(buf, numpy.uint8)
            a.shape = (self.surface_dims[0], self.surface_dims[1], 4)
            #Strip Alpha values and copy to our main numpy array
            numpy.copyto(self.data, a[:, :, :3])

            self.context.set_source_rgb(0, 0, 0)
            self.context.paint()

            ##UPDATE END

            self.signal_update_gui_and_boards()
            game_fps.cycle_complete()

            next_update += 1.0 / fps
            sleep_time = next_update - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    def refresh_sensor_data(self):
        fps = 10
        next_update = time.time()

        while not self._stop.isSet() and fps != 0:
            for bus in self.board_buses:
                bus.read_sensors()

            next_update += 1.0 / fps
            sleep_time = next_update - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

    def signal_update_gui_and_boards(self):
        self.update_flags = {'GUI': True}
        for bus in self.board_buses:
            bus.update()

    def find_board(self, board_id):
        for bus in self.board_buses:
            for board in bus:
                if board.id == board_id:
                    return board
        logging.warning("Board {} was looked for but not found.".format(board_id))
        return None

    def key_press(self, event):
        self.handle_key_change(event.char, True)

    def key_release(self, event):
        self.handle_key_change(event.char, False)

    def handle_key_change(self, key, override):
        for button in self.buttons:
            assert isinstance(button, BoardButton)
            if button.override_key == key:
                button.set_override(override)

    def assign_pong_keys_to_boardbuttons(self, pong_game):
        """
        Populates "buttons" list
        """

        #keyboard keys - which will be listened to
        override_keys = [
            'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ö'
        ]
        for i in range(int(len(override_keys)/2)):
            self.buttons.append(
                BoardButton(
                    board_id=128+i,
                    board_buses=self.board_buses,
                    function=pong_game.p2_paddle.set_target_position,
                    args=[10/2 + 10*i],
                    override_key=override_keys[i]
                )
            )
            self.buttons.append(
                BoardButton(
                    128+100-1-i,
                    self.board_buses,
                    pong_game.p1_paddle.set_target_position,
                    [10/2 + 10*(9-i)],
                    override_keys[20-1-i]
                )
            )

    def assign_breaker_keys_to_boardbuttons(self, breaker_game):
        """
        Populates "buttons" list
        """

        #keyboard keys - which will be listened to
        override_keys = [
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ö'
        ]
        for i in range(len(override_keys)):
            self.buttons.append(
                BoardButton(
                    128+100-1-i,
                    self.board_buses,
                    breaker_game.paddle.set_target_position,
                    [10/2 + 10*(9-i)],
                    override_keys[10-1-i]
                )
            )


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

        self.overridden = False   # Is button currently overridden?
        self.board = None
        self.warning_timer = time.time()

    def is_pressed(self):
        if self.board is None:
            for bus in self.board_buses:
                for board in bus.boards:
                    if board.id == self.board_id:
                        self.board = board
        #Still not found after searching
        if self.board is None:
            #If no buttons found after 1 second: Warn user
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
