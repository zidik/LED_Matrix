__author__ = 'Mark'

import tkinter
import logging

import serial
import PIL.Image
import PIL.ImageTk
import numpy
import threading
import time

import fpsManager
import ledBoard
import board_bus


class App(object):
    def __init__(self, master, **kwargs):

        self.master = master
        self.frame = tkinter.Frame(self.master, width=600, height=400)
        self.frame.pack()
        self.canvas = tkinter.Canvas(self.frame, width=500, height=400)
        self.canvas.pack()

        self.photo = None  #Holds TkInter image for displaying in GUI

        #Create random data
        brightness = 100
        self.data = numpy.array(numpy.random.random((10, 20, 3)) * brightness, dtype=numpy.uint8)
        self.data[1, 1] = numpy.array([255, 255, 255])



        serial_connections = [
            serial.Serial(port=2, baudrate=500000)
        ]

        # Create all buses
        self.board_buses = []

        for connection in serial_connections:
            update_fps_var = tkinter.StringVar()
            tkinter.Label(self.frame, textvariable=update_fps_var).pack()
            update_fps = fpsManager.FpsManager(
                string_var=update_fps_var,
                string_var_text=str(connection.name) + " update: {} FPS"
            )
            sensor_fps_var = tkinter.StringVar()
            tkinter.Label(self.frame, textvariable=sensor_fps_var).pack()
            sensor_fps = fpsManager.FpsManager(
                string_var=sensor_fps_var,
                string_var_text=str(connection.name) + " sensor: {} FPS"
            )
            new_bus = board_bus.BoardBus(connection, self.data, update_fps, sensor_fps)
            self.board_buses.append(new_bus)

        #Start bus threads

        for bus in self.board_buses:
            bus.start()

        '''
        number_of_boards = 4
        board_columns = 10

        self.board_buses = [
            [ledBoard.Board(128+number,serial_connections[0] , number % board_columns, number // board_columns) for number in range(0, number_of_boards)],
            []
        ]
        '''


        #GUI FPS
        gui_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=gui_fps_var).pack()
        self.gui_fps = fpsManager.FpsManager(string_var=gui_fps_var, string_var_text="GUI: {} FPS", update_period=0.5)
        #Game FPS
        game_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=game_fps_var).pack()
        self.game_fps = fpsManager.FpsManager(string_var=game_fps_var,  string_var_text="Game: {} FPS")
        #Serial FPS
        serial_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=serial_fps_var).pack()
        self.serial_fps = fpsManager.FpsManager(string_var=serial_fps_var,  string_var_text="Serial: {} FPS")

        self._stop = threading.Event()
        self.threads = [] #TODO:is this needed anymore?

        # Start "Game"-Loop - updates data for displaying
        t = threading.Thread(target=self.update_data)
        t.start()
        self.threads.append(t)

        # Start "Sensor Refresh"-Loop - updates sensor readings
        t = threading.Thread(target=self.refresh_sensor_data)
        t.start()
        self.threads.append(t)

        # Start "GUI image update"-Loop - updates sensor readings
        t = threading.Thread(target=self.refresh_GUI_image)
        t.start()
        self.threads.append(t)

        self.update_flags = {}
        self.refresh_gui_and_boards()

    def stop(self):
        self._stop.set()
        logging.info("Waiting for app threads to stop")
        for thread in self.threads:
            thread.join()
        logging.info("Threads stopped, Stopping board buses")
        for bus in self.board_buses:
            bus.stop()
        logging.info("Waiting for boardbus threads to stop")
        for bus in self.board_buses:
            if bus.isAlive():
                bus.join()
        logging.info("App stopped")


    #TODO: remove all this:
    def refresh_GUI_image(self):
        FPS = 100
        next_update = time.time()

        while not self._stop.isSet():
           #try:
                ## UPDATE
                if self.update_flags['GUI']:
                    self.update_flags['GUI'] = False

                    im = PIL.Image.fromarray(self.data)
                    im = im.resize((400, 200))
                    #TODO: Currently causes Crash :(
                    #self.photo = PIL.ImageTk.PhotoImage(image=im)
                    #self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)
                    self.gui_fps.cycle_complete()
                ##UPDATE END

                next_update += 1.0 / FPS
                sleeptime = next_update - time.time()
                if sleeptime > 0:
                    time.sleep(sleeptime)

    def update_data(self):
        FPS = 300
        next_update = time.time()

        while not self._stop.isSet():
           #try:
                ## UPDATE
                self.data = numpy.roll(self.data, -1, 1)
                self.refresh_gui_and_boards()
                ##UPDATE END
                self.game_fps.cycle_complete()

                next_update += 1.0 / FPS
                sleeptime = next_update - time.time()
                if sleeptime > 0:
                    time.sleep(sleeptime)

    def refresh_sensor_data(self):
        FPS = 1
        next_update = time.time()

        while not self._stop.isSet():
            for bus in self.board_buses:
                bus.read_sensors()

            next_update += 1.0 / FPS
            sleeptime = next_update - time.time()
            if sleeptime > 0:
                time.sleep(sleeptime)


    def refresh_gui_and_boards(self):
        self.update_flags = {'GUI': True}
        for bus in self.board_buses:
            bus.update()




