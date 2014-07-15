__author__ = 'Mark Laane'

import tkinter
import time

from PIL import Image
from PIL import ImageTk

from fpsManager import FpsManager
from game_controller import GameController
from matrix_controller import MatrixController


class GUIapp:
    def __init__(self, master, game_controller):
        assert isinstance(game_controller, GameController)
        self.game_controller = game_controller
        self.matrix_controller = self.game_controller.matrix_controller
        assert isinstance(self.matrix_controller, MatrixController)

        canvas_width = 300
        canvas_height = int(canvas_width / self.matrix_controller.dimensions[0] * self.matrix_controller.dimensions[1])
        self.canvas_dims = canvas_width, canvas_height

        self.master = master
        self.frame = tkinter.Frame(self.master, width=600, height=400)
        self.frame.pack()
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

        self.game_controller.connect("game changed", self.assign_keys)
        # Start refreshing GUI
        self.master.after(0, self._refresh_gui)

    def assign_keys(self, mode):
        override_keys = []
        if mode == GameController.Mode.pong:
            override_keys = [
                'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
                'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ö'
            ]
        if mode == GameController.Mode.breaker:
            override_keys = [
                'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ö'
            ]
        if mode == GameController.Mode.animation or \
                mode == GameController.Mode.catch_colors or \
                mode == GameController.Mode.catch_colors_2P:
            override_keys = [
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
                'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ö',
                'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '-'
            ]


        for i in range(len(self.matrix_controller.buttons)):
            assert(self.matrix_controller.dimensions[0] <= 10)  # Next line will break otherwise
            try:
                self.matrix_controller.buttons[i].override_key = override_keys[
                    i + i//self.matrix_controller.dimensions[0]*(10-self.matrix_controller.dimensions[0])
                ]
            except IndexError:
                break

    def update(self):
        self._data_updated = True

    def _refresh_gui(self):
        fps = 50
        next_update = time.time() + 1.0 / fps

        # Update displayed image if data has changed
        if self._data_updated:
            self._data_updated = False
            # Create image from numpy array
            im = Image.fromarray(self.matrix_controller.displayed_data)
            im = im.resize((self.canvas_dims[0], self.canvas_dims[1]))
            self.photo = ImageTk.PhotoImage(image=im)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)

            self.gui_fps.cycle_complete()

        # Update FPS
        self.update_gui_fps()
        self.update_bus_fps()
        self.update_sensor_fps()

        sleep_time = round((next_update - time.time()) * 1000)
        if sleep_time <= 0:
            sleep_time = 1  # sleep at least a little

        # Loop
        self.master.after(sleep_time, self._refresh_gui)

    def update_gui_fps(self):
        self.gui_fps_var.set("GUI fps={}".format(self.gui_fps.current_fps))

    def update_bus_fps(self):
        fps_string = ""
        for bus in self.matrix_controller.board_buses:
            fps_string += "{0} {LED update.current_fps} {Sensor poll.current_fps}\
             {Sensor response.current_fps}\n".format(bus.serial_connection.name, **bus.fps)
        self.bus_fps_var.set(fps_string)

    def update_sensor_fps(self):
        fps_string = ""
        for bus in self.matrix_controller.board_buses:
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
