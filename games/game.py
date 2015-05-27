__author__ = 'Mark'

import numpy
import cairocffi as cairo

class Game:
    """
    Abstract class for a game
    Game has to implement at least these methods
    """

    # This is here, so matrix_controller could differentiate between normal game and DirectNumpyAccessGame
    @property
    def needs_direct_numpy_access(self):
        return isinstance(self, DirectNumpyAccessGame)

    def step(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def draw(self, context: cairo.Context):
        raise NotImplementedError("Subclass must implement abstract method")


class DirectNumpyAccessGame(Game):
    """
    Abstract class for a game, that needs direct access to underlying numpy array.
    (And does not use Cairo for drawing)
    """

    def step(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def draw(self, displayed_data: numpy.ndarray):
        raise NotImplementedError("Subclass must implement abstract method")