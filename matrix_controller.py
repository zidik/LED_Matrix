__author__ = 'Mark'

import tkinter
import logging

import serial
import PIL.Image
import PIL.ImageTk
import numpy
import threading
import time
import random

import fpsManager
import board_bus

import pong


class App(object):
    def __init__(self, master, **kwargs):

        board_bus.BoardBus.board_assignment = [
            [128, 0, 0],
            [129, 1, 0],
            [130, 0, 1],
            [131, 1, 1]
        ]

        self.master = master
        self.frame = tkinter.Frame(self.master, width=600, height=400)
        self.frame.pack()
        self.canvas = tkinter.Canvas(self.frame, width=500, height=400)
        self.canvas.pack()

        self.photo = None  #Holds TkInter image for displaying in GUI

        #Create random data
        brightness = 100
        self.data = numpy.array(numpy.random.random((20, 20, 3)) * brightness, dtype=numpy.uint8)
        self.data[1, 1] = numpy.array([255, 255, 255])

        self.ball1 = pong.Ball(2, 4, 0.7, 1)
        self.ball2 = pong.Ball(2, 2, 1, 0.2)
        self.paddle = pong.Paddle(5, 0, 3)

        serial_connections = [
            serial.Serial(port=4, baudrate=500000)
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

        #Sensor value display
        self.sensor_gui_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=self.sensor_gui_var).pack()

        #GUI FPS
        gui_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=gui_fps_var).pack()
        self.gui_fps = fpsManager.FpsManager(string_var=gui_fps_var, string_var_text="GUI: {} FPS", update_period=0.5)
        #Game FPS
        game_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=game_fps_var).pack()
        self.game_fps = fpsManager.FpsManager(string_var=game_fps_var, string_var_text="Game: {} FPS")
        #Serial FPS
        serial_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=serial_fps_var).pack()
        self.serial_fps = fpsManager.FpsManager(string_var=serial_fps_var, string_var_text="Serial: {} FPS")

        self._stop = threading.Event()
        self.threads = []  #TODO:is this needed anymore?

        #"Game"-Loop - updates data for displaying
        t = threading.Thread(target=self.update_data)
        self.threads.append(t)

        #"Sensor Refresh"-Loop - updates sensor readings
        t = threading.Thread(target=self.refresh_sensor_data)
        self.threads.append(t)

        #"GUI image update"-Loop - updates sensor readings
        t = threading.Thread(target=self.refresh_GUI_image)
        self.threads.append(t)

        self.update_flags = {}
        self.refresh_gui_and_boards()

        for thread in self.threads:
            thread.start()

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
        FPS = 50
        next_update = time.time()

        while not self._stop.isSet():
            #try:
            ## UPDATE
            if self.update_flags['GUI']:
                self.update_flags['GUI'] = False

                im = PIL.Image.fromarray(self.data)
                im = im.resize((400, 200))
                #TODO: Currently causes Crash :(
                self.photo = PIL.ImageTk.PhotoImage(image=im)
                self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)
                self.gui_fps.cycle_complete()
            ##UPDATE END

            temp_gui_string = ""
            for bus in self.board_buses:
                for board in bus.boards:
                    temp_gui_string += str(board.sensor_value) + "\n"

            self.sensor_gui_var.set(temp_gui_string)

            next_update += 1.0 / FPS
            sleeptime = next_update - time.time()
            if sleeptime > 0:
                time.sleep(sleeptime)

    def update_data(self):
        FPS = 20
        next_update = time.time()

        while not self._stop.isSet() and FPS != 0:
            ## UPDATE

            ##RANDOM CHANGE
            #for i in range(10):
            #    self.data[random.randrange(0, 50), random.randrange(0, 50)] = numpy.array(numpy.random.random((3)) * brightness, dtype=numpy.uint8)

            self.ball1.step()
            self.ball2.step()

            self.data[:] = numpy.array([0, 0, 0])

            self.draw_guidlines()

            self.data[round(self.ball1.y), round(self.ball1.x)] = numpy.array([100, 100, 100])
            self.data[round(self.ball2.y), round(self.ball2.x)] = numpy.array([200, 0, 0])
            self.data[round(self.paddle.y), round(self.paddle.x-self.paddle.size/2):round(self.paddle.x+self.paddle.size/2)+1] = numpy.array([200, 0, 0])

            self.refresh_gui_and_boards()

            ##UPDATE END

            self.game_fps.cycle_complete()

            next_update += 1.0 / FPS
            sleeptime = next_update - time.time()
            if sleeptime > 0:
                time.sleep(sleeptime)

    def refresh_sensor_data(self):
        FPS = 10
        next_update = time.time()

        while not self._stop.isSet() and FPS != 0:
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

    def draw_guidlines(self):
        self.data[0:5, 0] = numpy.array([100] * 3)
        self.data[5, 0] = numpy.array([100, 0, 0])

        self.data[0:5, 10] = numpy.array([100] * 3)
        self.data[5, 10] = numpy.array([0, 100, 0])

        self.data[10:15, 0] = numpy.array([100] * 3)
        self.data[15, 0] = numpy.array([0, 0, 100])

        self.data[10:15, 10] = numpy.array([100] * 3)
        self.data[15, 10] = numpy.array([200, 200, 200])





