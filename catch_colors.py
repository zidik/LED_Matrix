import random

__author__ = 'Mark'

from operator import mul
import math
import time
import game
from game_elements_library import Circle

# "Cairocffi" could be also installed as "cairo"
try:
    import cairocffi as cairo
except ImportError:
    import cairo


class CatchColors2P(game.Game):
    def __init__(self, board_assignment):
        self._board_assignment = board_assignment
        self._P1_symbol = None
        self._P2_symbol = None

    def button_pressed(self, board_id):
        """
        Signal the game that the button was pressed.

        :param board_id: number of the board-button pressed.
        """
        if self._P1_symbol.board_id == board_id:

            self._reset_symbols()

    def _reset_symbols(self):
        #P1 Symbol
        board_id, x, y = random.choice(self._board_assignment)
        self._P1_symbol = Symbol(center_x=x * 10 + 5, center_y=y * 10 + 5, board_id=board_id)
        #P2 Symbol
        board_id, x, y = random.choice(self._board_assignment)
        self._P2_symbol = Symbol(center_x=x * 10 + 5, center_y=y * 10 + 5, board_id=board_id)


class PointsBar():
    def __init__(self, max_points, color,  start_point, end_point):
        self.points = 0
        self.max_points = max_points
        self.color = color
        self.start_point = start_point
        self.end_point = end_point

    def draw(self, ctx):
        ctx.move_to(*self.start_point)
        ctx.line_to(*self.end_point)
        ctx.set_source_rgba(0, 0, 0, 0)
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
        #Clear Background
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
        r, g, b, a = self.color
        
        ctx.set_source(cairo.SolidPattern(b, g, r, a))
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
        return time.time()-self.born

    @property
    def is_alive(self):
        return self.age <= FadingSymbol.lifetime

    def draw(self, ctx):
        weight = min(1, self.age/FadingSymbol.change_period)
        self.color = tuple(
            sum(map(mul, x, (1-weight, weight))) for x in zip(FadingSymbol.color_start, FadingSymbol.color_end)
        )
        super().draw(ctx)

