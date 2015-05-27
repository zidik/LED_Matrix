import math

from games import game


__author__ = 'Mark'

import numpy

class Plasma(game.DirectNumpyAccessGame):
    def __init__(self, board_assignment, surface_dims):
        nx, ny = surface_dims

        x = numpy.linspace(0, 1*2*numpy.pi, nx, endpoint=False)
        y = numpy.linspace(0, 1*2*numpy.pi, ny, endpoint=False)
        self.xv, self.yv = numpy.meshgrid(x, y)

        #Integer version
        #self.x_sin = numpy.asarray((numpy.sin(xv)/2+0.5)*255, numpy.uint8)
        #self.y_sin = numpy.asarray((numpy.sin(yv)/2+0.5)*255, numpy.uint8)

        #Float version
        self.x_sin = numpy.sin(self.xv)
        self.y_sin = numpy.sin(self.yv)


        self.board_assignment = board_assignment
        self.time = 0.0


    def step(self):
        self.time+=1

        self.x_sin = numpy.roll(self.x_sin, shift=1, axis=1)
        self.y_sin = numpy.roll(self.y_sin, shift=2, axis=0)

        cx = self.xv+0.5*numpy.sin(self.time/14)
        cy = self.yv+0.5*numpy.cos(self.time/32)
        self.c_sin = numpy.sin(numpy.sqrt(10*((cx-4)**2+(cy-4)**2)+1)+self.time)

    def draw(self, displayed_data: numpy.array):
        ratio = 2/3

        sinsum = self.x_sin*ratio + self.y_sin*(1-ratio)
        sinsum = self.c_sin

        #red = numpy.ones(sinsum.shape)*255
        #green = (numpy.cos(sinsum*numpy.pi)/2 + 0.5) * 255
        #blue = (numpy.sin(sinsum*numpy.pi)/2 + 0.5) * 255

        red = numpy.zeros(sinsum.shape)
        green = numpy.zeros(sinsum.shape)
        blue = (sinsum/2 + 0.5) * 255

        displayed_data[:, :, 0] = red
        displayed_data[:, :, 1] = green
        displayed_data[:, :, 2] = blue

    def button_pressed(self, board_id):
        """
        Signal the game that the button was pressed.

        :param board_id: number of the board-button pressed.
        """

        for board_id_found, x, y in self.board_assignment:
            pass
        else:
            raise ValueError("No board found with id {}".format(board_id))