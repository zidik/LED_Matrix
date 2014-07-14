import random

__author__ = 'Mark'

from operator import mul, sub, add
from enum import Enum
from threading import Thread
import math
import time
import game
from game_elements_library import Circle, delayed_function_call

# "Cairocffi" could be also installed as "cairo"
try:
    import cairocffi as cairo
except ImportError:
    import cairo


class CatchColors2P(game.Game):
    class State(Enum):
        running = 1
        finished = 2


    max_points = 21
    P1_color = (0.0, 1.0, 0.0, 1.0)
    P2_color = (0.0, 0.0, 1.0, 1.0)

    def __init__(self, board_assignment, surface_dims):
        self._board_assignment = board_assignment
        self._P1_symbol = None
        self._P2_symbol = None
        self._P1_points = 0
        self._P2_points = 0
        self._state = CatchColors2P.State.running

        max_points = CatchColors2P.max_points
        color = CatchColors2P.P1_color
        x, y = surface_dims
        self._P1_points_bars = [
            PointsBar(max_points, color, (0, 0), (0, y - 1 - 2)),
            PointsBar(max_points, color, (0, y - 1), (x - 1 - 2, y - 1)),
            PointsBar(max_points, color, (x - 1, y - 1), (x - 1, 0 + 2)),
            PointsBar(max_points, color, (x - 1, 0), (0 + 2, 0))
        ]
        color = CatchColors2P.P2_color
        self._P2_points_bars = [
            PointsBar(max_points, color, (0 + 1, 0), (0 + 1, y - 1 - 2)),
            PointsBar(max_points, color, (0, y - 1 - 1), (x - 1 - 2, y - 1 - 1)),
            PointsBar(max_points, color, (x - 1 - 1, y), (x - 1 - 1, 0 + 2)),
            PointsBar(max_points, color, (x - 1, 0 + 1), (+2, 0 + 1)),
        ]

        self._reset_game()

    def _reset_game(self):
        self._P1_points = 0
        self._P2_points = 0
        for bar in self._P1_points_bars + self._P2_points_bars:
            bar.points = 0
        self._reset_symbols()
        self._state = CatchColors2P.State.running

    def button_pressed(self, board_id):
        """
        Signal the game that the button was pressed.

        :param board_id: number of the board-button pressed.
        """

        if self._P1_symbol.board_id == board_id:
            self._P1_points += 1
            for bar in self._P1_points_bars:
                bar.points = self._P1_points
            self._reset_symbols()

        if self._P2_symbol.board_id == board_id:
            self._P2_points += 1
            for bar in self._P2_points_bars:
                bar.points = self._P2_points
            self._reset_symbols()

        if self._P1_points == CatchColors2P.max_points or self._P2_points == CatchColors2P.max_points:
            self._state = CatchColors2P.State.finished
            Thread(target=delayed_function_call, args=(2, self._reset_game)).start()

    def step(self):
        pass

    def draw(self, ctx):
        if self._state == CatchColors2P.State.finished:
            # Show winner color
            if self._P1_points == CatchColors2P.max_points:
                color = CatchColors2P.P1_color
            elif self._P2_points == CatchColors2P.max_points:
                color = CatchColors2P.P2_color
            else:
                return
            ctx.set_source_rgba(color)
            ctx.paint()
        else:
            # Clear Background
            ctx.set_source_rgb(0, 0, 0)
            ctx.paint()

            self._P1_symbol.draw(ctx)
            self._P2_symbol.draw(ctx)

            for bar in self._P1_points_bars + self._P2_points_bars:
                bar.draw(ctx)

    def _reset_symbols(self):
        # P1 Symbol
        board_id, x, y = random.choice(self._board_assignment)
        self._P1_symbol = Symbol(center_x=x * 10 + 5, center_y=y * 10 + 5, board_id=board_id,
                                 color=CatchColors2P.P1_color)
        #P2 Symbol
        board_id, x, y = random.choice(self._board_assignment)
        self._P2_symbol = Symbol(center_x=x * 10 + 5, center_y=y * 10 + 5, board_id=board_id,
                                 color=CatchColors2P.P2_color)


class PointsBar():
    def __init__(self, max_points, color, start_point, end_point):
        self.points = 0
        self._max_points = max_points
        self._color = color
        self._start_point = start_point
        self._end_point = end_point

    @property
    def _curr_point(self):
        length = self.points / self._max_points  # how much points relative to max
        diff = map(sub, self._end_point, self._start_point)
        vect = [coord * length for coord in diff]
        return map(add, self._start_point, vect)

    @staticmethod
    def _correct_line(p1, p2):
        """
        This corrects line endpoints for drawing with cairo.
        (moves line 0.5px sideways and the further point by 1px further)
        """
        p1 = list(p1)
        p2 = list(p2)
        # Cairo draws sharp lines only if coordinates are aligned to half values
        if p1[0] == p2[0]:
            # Vertical line:
            p1[0] += 0.5
            p2[0] += 0.5
            if p1[1] < p2[1]:
                p2[1] += 1
            else:
                p1[1] += 1
        elif p1[1] == p2[1]:
            # Horizontal line:
            p1[1] += 0.5
            p2[1] += 0.5
            if p1[0] < p2[0]:
                p2[0] += 1
            else:
                p1[0] += 1
        return p1, p2

    def draw(self, ctx):
        start_point, curr_point = PointsBar._correct_line(self._start_point, self._curr_point)
        ctx.move_to(*start_point)
        ctx.line_to(*curr_point)
        ctx.set_source_rgba(*self._color)
        ctx.set_line_width(1)
        ctx.stroke()


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

