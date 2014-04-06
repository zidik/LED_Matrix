__author__ = 'Mark'

import tkinter
import logging
import threading
import time

import serial
import PIL.Image
import PIL.ImageTk
import numpy

import fpsManager
import board_bus
import pong


class App(object):
    def __init__(self, master):

        board_bus.BoardBus.board_assignment = [
            [128, 0, 0],
            [129, 1, 0],
            [130, 0, 1],
            [131, 1, 1]
        ]

        self.canvas_dims = 200, 200

        master.bind_all('<Escape>', lambda event: event.widget.quit())
        self.master = master
        self.frame = tkinter.Frame(self.master, width=600, height=400)
        self.frame.pack()
        self.canvas = tkinter.Canvas(self.frame, width=self.canvas_dims[0], height=self.canvas_dims[1])
        self.canvas.pack()

        self.photo = None  # Holds TkInter image for displaying in GUI

        self.data = numpy.zeros((20, 20, 3), dtype=numpy.uint8)

        serial_connections = []
        try:
            serial_connections.append(serial.Serial(port=3, baudrate=500000))
        except serial.SerialException as e:
            logging.warning("Unable to open serial port")
            logging.exception(e)

        #List of fps objects about app (whitch need periodical refreshing)
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
        logging.debug("Waiting for boardbus threads to stop")
        for bus in self.board_buses:
            if bus.isAlive():
                bus.join()
        logging.debug("App stopped")

    def draw_board(self):
        row_nr = 0
        col_nr = 0
        size = 10
        self.canvas.delete(tkinter.ALL)
        for row in self.data:
            for cell in row:
                color_string = "#"
                for color_element in cell:
                    color_string += "%0.2X" % color_element
                self.canvas.create_rectangle(
                    col_nr*size, row_nr*size, (col_nr+1)*size, (row_nr+1)*size+1,
                    fill=color_string
                )
                col_nr += 1
            col_nr = 0
            row_nr += 1

    #TODO: remove all this:
    def _refresh_gui(self):
        fps = 30
        next_update = time.time()

        ## UPDATE
        if self.update_flags['GUI']:
            self.update_flags['GUI'] = False
            #TODO: Currently causes Crash :(
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
        fps = 20

        #Game FPS
        game_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=game_fps_var).pack()
        game_fps = fpsManager.FpsManager(string_var=game_fps_var, string_var_text="Game: {} FPS")
        self.app_fps_list.append(game_fps)

        next_update = time.time()

        pong_game = pong.Pong(
            (
                BoardButton(130, self.board_buses),
                BoardButton(131, self.board_buses),
                BoardButton(129, self.board_buses),
                BoardButton(128, self.board_buses)
            )
        )


        while not self._stop.isSet() and fps != 0:
            ## UPDATE
            self.data[:] = numpy.array([0, 0, 0])
            #self.draw_guidelines()
            pong_game.step()
            pong_game.draw(self.data)
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

    def draw_guidelines(self):
        self.data[0:5, 0] = numpy.array([100] * 3)
        self.data[5, 0] = numpy.array([100, 0, 0])

        self.data[0:5, 10] = numpy.array([100] * 3)
        self.data[5, 10] = numpy.array([0, 100, 0])

        self.data[10:15, 0] = numpy.array([100] * 3)
        self.data[15, 0] = numpy.array([0, 0, 100])

        self.data[10:15, 10] = numpy.array([100] * 3)
        self.data[15, 10] = numpy.array([70, 70, 0])

        self.data[20:25, 0] = numpy.array([100] * 3)
        self.data[25, 0] = numpy.array([0, 70, 70])

        self.data[20:25, 10] = numpy.array([100] * 3)
        self.data[25, 10] = numpy.array([70, 0, 70])


class BoardButton:
    """
        Tries to find correct board and then returns it's button's state
    """
    def __init__(self, board_id, board_buses):
        self.board_id = board_id
        self.board_buses = board_buses
        self.board = None
        self.warning_timer = time.time()

    def is_pressed(self):
        if self.board is None:
            for bus in self.board_buses:
                for board in bus.boards:
                    if board.id == self.board_id:
                        self.board = board
        if self.board is None:
            #If no buttons found after 1 second: Warn user
            if self.warning_timer is not None and time.time() - self.warning_timer > 1.0:
                logging.warning("BoardButton {} not found".format(self.board_id))
                self.warning_timer = None
            return False
        return self.board.is_button_pressed()








