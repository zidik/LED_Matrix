__author__ = 'Mark Laane'

import tkinter
from enum import Enum
import time

import PIL.Image
import PIL.ImageTk

from fpsManager import FpsManager
from board_bus import BoardBus
from breaker import Breaker
from pong import Pong
from test_pattern import TestPattern


class GUIapp:
    class Mode(Enum):
        test = 0
        pong = 1
        breaker = 2

    def __init__(self, master, matrix_controller):
        self.mode = GUIapp.Mode.pong
        self.matrix_controller = matrix_controller
        self.canvas_dims = 300, 300

        self.master = master
        self.frame = tkinter.Frame(self.master, width=600, height=400)
        self.frame.pack()  # (fill=tkinter.BOTH, expand=1) TODO?
        self.canvas = tkinter.Canvas(self.frame, width=self.canvas_dims[0], height=self.canvas_dims[1])
        self.canvas.pack()

        self.photo = None  # Holds TkInter image for displaying in GUI

        self.master.bind_all('<Escape>', lambda event: event.widget.quit())
        self.frame.bind("<Key>", self.key_press)
        self.frame.bind("<KeyRelease>", self.key_release)
        self.frame.focus_set()

        self._data_updated = False
        self._stop = False

        # GUI FPS
        self.gui_fps = FpsManager()
        self.gui_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=self.gui_fps_var).pack()

        # Bus FPS
        self.bus_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=self.bus_fps_var).pack()
        # Sensor FPS
        self.sensor_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=self.sensor_fps_var).pack()

        self.start_game()
        # Start refreshing GUI
        self.master.after(0, self._refresh_gui)

    def start_game(self):
        if self.mode == GUIapp.Mode.test:
            self.matrix_controller.game = TestPattern(
                self.matrix_controller.surface_dims, BoardBus.board_assignment, self.matrix_controller.board_buses
            )
        elif self.mode == GUIapp.Mode.pong:
            self.matrix_controller.game = Pong(self.matrix_controller.surface_dims)
            self.assign_pong_keys_to_boardbuttons(self.matrix_controller.game)
        elif self.mode == GUIapp.Mode.breaker:
            self.matrix_controller.game = Breaker(self.matrix_controller.surface_dims)
            self.assign_breaker_keys_to_boardbuttons(self.matrix_controller.game)

    def update(self):
        self._data_updated = True

    def _refresh_gui(self):
        fps = 50
        next_update = time.time() + 1.0 / fps

        # Update displayed image if data has changed
        if self._data_updated:
            self._data_updated = False
            # Create image from numpy array
            im = PIL.Image.fromarray(self.matrix_controller.displayed_data)
            im = im.resize((self.canvas_dims[0], self.canvas_dims[1]))
            self.photo = PIL.ImageTk.PhotoImage(image=im)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)

            self.gui_fps.cycle_complete()

        # Update FPS
        self.update_gui_fps()
        self.update_bus_fps()
        self.update_sensor_fps()

        sleep_time = round((next_update - time.time()) * 1000)
        if sleep_time <= 0:
            sleep_time = 1  # sleep at least a little

        #Loop
        self.master.after(sleep_time, self._refresh_gui)

    def update_gui_fps(self):
        self.gui_fps_var.set("GUI fps={}".format(self.gui_fps.current_fps))

    def update_bus_fps(self):
        fps_string = ""
        for bus in self.matrix_controller.board_buses:
            assert isinstance(bus, BoardBus)
            fps_string += "{0} {LED update.current_fps} {Sensor poll.current_fps} {Sensor response.current_fps}\n".format(
                bus.serial_connection.name, **bus.fps)
        self.bus_fps_var.set(fps_string)

    def update_sensor_fps(self):
        fps_string = ""
        for bus in self.matrix_controller.board_buses:
            assert isinstance(bus, BoardBus)
            for board in bus.boards:
                fps_string += "id={id} sensor={sensor}\n".format(id=board.id, sensor=board.sensor_value)
        self.sensor_fps_var.set(fps_string)

    def key_press(self, event):
        self.handle_key_change(event.char, True)

    def key_release(self, event):
        self.handle_key_change(event.char, False)

    def handle_key_change(self, key, override):
        for button in self.matrix_controller.buttons:
            if button.override_key == key:
                button.set_override(override)

    def assign_pong_keys_to_boardbuttons(self, pong_game):
        """
        Populates "buttons" list
        """

        # keyboard keys - which will be listened to
        override_keys = [
            'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ö'
        ]
        for i in range(int(len(override_keys) / 2)):
            self.matrix_controller.add_button(
                board_id=128 + i,
                function=pong_game.p2_paddle.set_target_position,
                args=[10 / 2 + 10 * i],
                override_key=override_keys[i]
            )
            self.matrix_controller.add_button(
                128 + 100 - 1 - i,
                pong_game.p1_paddle.set_target_position,
                [10 / 2 + 10 * (9 - i)],
                override_keys[20 - 1 - i]
            )

    def assign_breaker_keys_to_boardbuttons(self, breaker_game):
        """
        Populates "buttons" list
        """

        # keyboard keys - which will be listened to
        override_keys = [
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ö'
        ]
        for i in range(len(override_keys)):
            self.matrix_controller.add_button(
                128 + 100 - 1 - i,
                breaker_game.paddle.set_target_position,
                [10 / 2 + 10 * (9 - i)],
                override_keys[10 - 1 - i]
            )
