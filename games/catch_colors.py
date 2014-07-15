import random

from games import game


__author__ = 'Mark'

from operator import mul, sub, add
from enum import Enum
from threading import Thread
import math
import time
from games.game_elements_library import Circle, delayed_function_call


class CatchColorsPlayer:
    def __init__(self, color, number, max_points, surface_dims):
        self.color = color

        self.symbol = None
        self._points = 0
        x, y = surface_dims
        self.points_bars = [
            PointsBar(max_points, color, (0 + number, 0), (0 + number, y - 1 - 2)),
            PointsBar(max_points, color, (0, y - 1 - number), (x - 1 - 2, y - 1 - number)),
            PointsBar(max_points, color, (x - 1 - number, y - 1), (x - 1 - number, 0 + 2)),
            PointsBar(max_points, color, (x - 1, 0 + number), (0 + 2, 0 + number))
        ]

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, value):
        self._points = value
        for bar in self.points_bars:
            bar.points = self._points


class CatchColors2P(game.Game):
    class State(Enum):
        running = 1
        finishing = 2
        finished = 3

    max_points = 21
    player_colors = [(0.0, 1.0, 0.0, 1.0), (0.0, 0.0, 1.0, 1.0)]

    def __init__(self, board_assignment, surface_dims):
        self._board_assignment = board_assignment

        self._state = CatchColors2P.State.running
        number_of_players = 2
        self.players = [
            CatchColorsPlayer(color, number, CatchColors2P.max_points, surface_dims)
            for color, number
            in zip(CatchColors2P.player_colors, range(number_of_players))
        ]

        # Used in resetting symbols to avoid boards/buttons, that are currently pressed
        self.pressed_buttons_last_step = []  #Remember buttons pressed since last step

        self._reset_game()

    def _reset_game(self):
        for player in self.players:
            player.points = 0
            player.symbol = None

        self._state = CatchColors2P.State.running

    def button_pressed(self, board_id):
        """
        Signal the game that the button was pressed.

        :param board_id: number of the board-button pressed.
        """

        self.pressed_buttons_last_step.append(board_id)

        if self._state != CatchColors2P.State.running:
            return

        for player in self.players:
            if player.symbol is None:
                continue
            if player.symbol.board_id == board_id:
                player.points += 1
                # Clear all player's symbols
                for p in self.players:
                    p.symbol = None

                if player.points >= CatchColors2P.max_points:
                    # Won!
                    self._state = CatchColors2P.State.finishing
                    Thread(target=delayed_function_call, args=(2, self._reset_game)).start()

    def step(self):
        if any([player.symbol is None for player in self.players]):
            self._reset_symbols()

        self.pressed_buttons_last_step = []

    def draw(self, ctx):
        if self._state == CatchColors2P.State.finished:
            for player in self.players:
                if player.points == CatchColors2P.max_points:
                    # Show winner color - Fade
                    r, g, b, _ = player.color
                    ctx.set_source_rgba(r, g, b, 0.1)
                    ctx.paint()
        else:
            if self._state == CatchColors2P.State.finishing:
                # This is here to ensure last frame of the game is also drawn before fading away to winner color
                self._state = CatchColors2P.State.finished
            # Clear Background
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()

            for player in self.players:
                player.symbol.draw(ctx)
                for bar in player.points_bars:
                    bar.draw(ctx)

    def _reset_symbols(self):
        # Next symbol can only be on board that currently is not stepped on
        choice_list = [
            assignment for assignment in self._board_assignment
            if not assignment[0] in self.pressed_buttons_last_step
        ]
        try:
            # Choose random boards and create symbols on them
            chosen_boards = random.sample(choice_list, len(self.players))
            for player, (board_id, x, y) in zip(self.players, chosen_boards):
                player.symbol = Symbol(center_x=x * 10 + 5, center_y=y * 10 + 5, board_id=board_id, color=player.color)
        except ValueError:
            # Currently not enough suitable boards to put symbols on
            pass


class PointsBar():
    def __init__(self, max_points, color, start_point, end_point):
        self.points = 0
        self._max_points = max_points
        self._color = color
        self._start_point = start_point
        self._end_point = end_point
        self.width = 1

    @property
    def _curr_point(self):
        length = self.points / self._max_points  # how much points relative to max
        diff = map(sub, self._end_point, self._start_point)
        vect = [coord * length for coord in diff]
        curr_point = list(map(add, self._start_point, vect))
        return curr_point

    @property
    def _curr_length(self):
        diff = list(map(sub, self._end_point, self._start_point))  # Vector pointing from start point to endpoint
        max_length = (diff[0] ** 2 + diff[1] ** 2) ** 0.5
        curr_length = max_length * (self.points / self._max_points)
        return curr_length

    def draw(self, ctx):
        ctx.set_source_rgba(*self._color)
        if self._start_point[0] == self._end_point[0]:
            if self._start_point[1] <= self._end_point[1]:
                ctx.rectangle(self._start_point[0], self._start_point[1], self.width, int(self._curr_length))
            else:
                ctx.rectangle(self._start_point[0], self._start_point[1] + 1, self.width, -int(self._curr_length))
        elif self._start_point[1] == self._end_point[1]:
            if self._start_point[0] <= self._end_point[0]:
                ctx.rectangle(self._start_point[0], self._start_point[1], int(self._curr_length), self.width)
            else:
                ctx.rectangle(self._start_point[0] + 1, self._start_point[1], -int(self._curr_length), self.width)
        else:
            raise ValueError("PointsBar has to be horizontal or vertical")

        ctx.fill()


class CatchColors(game.Game):
    """
    One player game where the player has to press the board which has the symbol on it
    """

    def __init__(self, board_assignment):
        self._board_assignment = board_assignment
        self._symbol = None

    def button_pressed(self, board_id):
        """
        Signal the game that the button was pressed.

        :param board_id: number of the board-button pressed.
        """
        if self._symbol is None:
            return

        if self._symbol.board_id == board_id:
            self._new_symbol()

    def step(self):
        if self._symbol is None:
            self._new_symbol()
        elif not self._symbol.is_alive:
            self._symbol = None
        else:
            pass

    def draw(self, ctx):
        # Clear Background
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()

        if self._symbol is not None:
            self._symbol.draw(ctx)

    def _new_symbol(self):
        board_id, x, y = random.choice(self._board_assignment)
        self._symbol = FadingSymbol(center_x=x * 10 + 5, center_y=y * 10 + 5, board_id=board_id)


class Symbol(Circle):
    def __init__(self, center_x, center_y, board_id, color):
        radius = 4.5
        super().__init__(center_x, center_y, radius)
        self.board_id = board_id
        self.color = color

    def draw(self, ctx):
        ctx.arc(self.center_x, self.center_y, self.radius, 0, 2 * math.pi)
        ctx.set_line_width(1)
        ctx.set_source_rgba(*self.color)
        ctx.fill()


class FadingSymbol(Symbol):
    color_start = (0, 1, 0, 1)
    color_end = (1, 0, 0, 1)
    lifetime = 4
    change_period = float(3)

    def __init__(self, center_x, center_y, board_id):
        super().__init__(center_x, center_y, board_id, color=None)
        self.born = time.time()

    @property
    def age(self):
        return time.time() - self.born

    @property
    def is_alive(self):
        return self.age <= FadingSymbol.lifetime

    def draw(self, ctx):
        weight = min(1, self.age / FadingSymbol.change_period)
        self.color = tuple(
            sum(map(mul, x, (1 - weight, weight))) for x in zip(FadingSymbol.color_start, FadingSymbol.color_end)
        )
        super().draw(ctx)

