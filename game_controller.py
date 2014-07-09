__author__ = 'Mark'
from enum import Enum
import logging

from board_bus import BoardBus
from breaker import Breaker
from pong import Pong
from test_pattern import TestPattern
from logo_bounce import LogoBounce
from animation import Animation
from catch_colors import CatchColors


class GameController:
    class Mode(Enum):
        nothing = -1
        test = 0
        pong = 1
        breaker = 2
        animation = 3
        logo = 4
        catch_colors = 5

    def __init__(self, matrix_controller):
        self.matrix_controller = matrix_controller
        self._call_on_game_change = list()

    def set_game_mode(self, mode):
        logging.info("Game set to {}".format(mode))
        surface_dims = self.matrix_controller.surface_dims
        if mode == GameController.Mode.nothing:
            self.matrix_controller.clear_displayed_data()
            self.matrix_controller
            game = None

        elif mode == GameController.Mode.test:
            game = TestPattern(surface_dims, BoardBus.board_assignment, self.matrix_controller.board_buses)

        elif mode == GameController.Mode.pong:
            game = Pong(surface_dims)
            self._add_pong_buttons(game)

        elif mode == GameController.Mode.breaker:
            game = Breaker(surface_dims)
            self._add_breaker_buttons(game)

        elif mode == GameController.Mode.animation:
            game = Animation(BoardBus.board_assignment)
            self._add_all_buttons(game)

        elif mode == GameController.Mode.logo:
            with open("logo.png", "rb") as logo_image:
                game = LogoBounce(surface_dims, logo_image)

        elif mode == GameController.Mode.catch_colors:
            game = CatchColors(BoardBus.board_assignment)
            self._add_all_buttons(game)

        else:
            raise ValueError("Unknown game mode")

        # notify all of change
        for func in self._call_on_game_change:
            func(mode, game)

        self.matrix_controller.game = game

    def connect(self, event, function):
        if event == "game changed":
            self._call_on_game_change.append(function)

    def _add_pong_buttons(self, game):
        self.matrix_controller.buttons = []
        assert isinstance(game, Pong)
        for i in range(10):
            #P2 buttons
            self.matrix_controller.add_button(
                board_id=128+i,
                function=game.button_pressed,
                args=[2, i]
            )
        for i in range(10):
            #P1 buttons
            self.matrix_controller.add_button(
                board_id=128+90+i,
                function=game.button_pressed,
                args=[1, i]
            )

    def _add_breaker_buttons(self, game):
        self.matrix_controller.buttons = []
        assert isinstance(game, Breaker)
        for i in range(10):
            self.matrix_controller.add_button(
                board_id=128+90+i,
                function=game.button_pressed,
                args=[i]
            )

    def _add_all_buttons(self, game):
        self.matrix_controller.buttons = []
        for i in range(100):
            self.matrix_controller.add_button(
                board_id=128+i,
                function=game.button_pressed,
                args=[128+i]
            )