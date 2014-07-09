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

    def draw(self, cairo_context):
        if self._symbol is not None:
            self._symbol.draw(cairo_context)

    def _new_symbol(self):
        board_id, x, y = random.choice(self._board_assignment)
        self._symbol = Symbol(center_x=x * 10 + 5, center_y=y * 10 + 5, board_id=board_id)


class Symbol(Circle):
    color_start = (0, 1, 0, 1)
    color_end = (1, 0, 0, 1)
    lifetime = 4
    change_period = float(3)

    def __init__(self, center_x, center_y, board_id):
        radius = 4.5
        super().__init__(center_x, center_y, radius)
        self.board_id = board_id
        self.born = time.time()

    @property
    def age(self):
        return time.time()-self.born

    @property
    def is_alive(self):
        return self.age <= Symbol.lifetime

    def draw(self, cairo_context):
        cairo_context.arc(self.center_x, self.center_y, self.radius, 0, 2 * math.pi)
        cairo_context.set_line_width(1)
        weight = min(1, self.age/Symbol.change_period)
        r, g, b, a = tuple(sum(map(mul, x, (1-weight, weight))) for x in zip(Symbol.color_start, Symbol.color_end))
        cairo_context.set_source(cairo.SolidPattern(b, g, r, a))
        cairo_context.fill()

