__author__ = 'Mark'
from enum import Enum, unique
import logging

from board_bus import BoardBus
from matrix_controller import MatrixController
from games import Animation, Breaker, CatchColors, CatchColorsMultiplayer, LogoBounce, Pong, TestPattern


class GameController:
    @unique
    class Mode(Enum):
        test = 0
        pong = 1
        breaker = 2
        animation = 3
        logo = 4
        catch_colors = 5
        catch_colors_multiplayer = 6

    def __init__(self, matrix_controller):
        assert isinstance(matrix_controller, MatrixController)
        self.matrix_controller = matrix_controller
        self._call_on_game_change = list()
        self.current_mode = GameController.Mode.test

    def reset_game(self):
        self.set_game_mode(self.current_mode)

    def set_game_mode(self, mode):
        self.current_mode = mode
        logging.info("Game set to {}".format(mode))
        surface_dims = self.matrix_controller.surface_dims  # Floor dimensions in pixels
        matrix_dims = self.matrix_controller.dimensions  # Floor dimensions in boards

        if mode == GameController.Mode.test:
            game = TestPattern(matrix_dims, BoardBus.board_assignment, self.matrix_controller.board_buses)

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

        elif mode == GameController.Mode.catch_colors_multiplayer:
            game = CatchColorsMultiplayer(BoardBus.board_assignment, surface_dims)
            self._add_all_buttons(game)

        else:
            raise ValueError("Unknown game mode")

        # notify all of change
        for func in self._call_on_game_change:
            func(mode)

        self.matrix_controller.game = game

    def connect(self, event, function):
        if event == "game changed":
            self._call_on_game_change.append(function)

    def _add_pong_buttons(self, game):
        self.matrix_controller.buttons = []
        assert isinstance(game, Pong)
        dimensions = self.matrix_controller.dimensions
        for i in range(dimensions[0]):
            # P2 buttons
            self.matrix_controller.add_button(
                board_id=128 + i,
                function=game.button_pressed,
                args=[2, i]
            )
        for i in range(10):
            # P1 buttons
            self.matrix_controller.add_button(
                board_id=128 + dimensions[0]*(dimensions[1]-1) + i,
                function=game.button_pressed,
                args=[1, i]
            )

    def _add_breaker_buttons(self, game):
        self.matrix_controller.buttons = []
        assert isinstance(game, Breaker)
        for i in range(10):
            self.matrix_controller.add_button(
                board_id=128 + 90 + i,
                function=game.button_pressed,
                args=[i]
            )

    def _add_all_buttons(self, game):
        self.matrix_controller.buttons = []
        for i in range(100):
            self.matrix_controller.add_button(
                board_id=128 + i,
                function=game.button_pressed,
                args=[128 + i]
            )