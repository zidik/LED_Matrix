__author__ = 'Mark'
from enum import Enum
import logging

from board_bus import BoardBus
from breaker import Breaker
from pong import Pong
from test_pattern import TestPattern
from logo_bounce import LogoBounce
from animation import Animation


class GameController:
    class Mode(Enum):
        nothing = -1
        test = 0
        pong = 1
        breaker = 2
        animation = 3
        logo = 4

    def __init__(self, matrix_controller):
        self.matrix_controller = matrix_controller
        self._call_on_game_change = list()

    def set_game_mode(self, mode):
        logging.info("Game set to {}".format(mode))
        surface_dims = self.matrix_controller.surface_dims
        if mode == GameController.Mode.nothing:
            game = None
        elif mode == GameController.Mode.test:
            game = TestPattern(surface_dims, BoardBus.board_assignment, self.matrix_controller.board_buses)
        elif mode == GameController.Mode.pong:
            game = Pong(surface_dims)
        elif mode == GameController.Mode.breaker:
            game = Breaker(surface_dims)
        elif mode == GameController.Mode.animation:
            game = Animation(BoardBus.board_assignment)
        elif mode == GameController.Mode.logo:
            with open("logo.png", "rb") as logo_image:
                game = LogoBounce(surface_dims, logo_image)
        else:
            raise ValueError("Unknown game mode")

        # notify all of change
        for func in self._call_on_game_change:
            func(mode, game)

        self.matrix_controller.game = game

    def call_on_game_change(self, function):
        self._call_on_game_change.append(function)