import random
import math

__author__ = 'Mark'

import game

# "Cairocffi" could be also installed as "cairo"
try:
    import cairocffi as cairo
except ImportError:
    import cairo

from game_elements_library import Circle, Moving


class Animation(game.Game):
    def __init__(self, board_assignment):
        self.board_assignment = board_assignment
        self.expanding_circles = []

    def step(self):
        for circle in self.expanding_circles:
            if circle.dead:
                self.expanding_circles.remove(circle)
            else:
                circle.step()

    def draw(self, context):
        for circle in self.expanding_circles:
            circle.draw(context)

    def button_pressed(self, board_id):
        """
        Signal the game that the button was pressed.

        :param board_id: number of the board-button pressed.
        """

        for board_id_found, x, y in self.board_assignment:
            if board_id_found == board_id:
                self.expanding_circles.append(ExpandingCircle(x * 10 + 5, y * 10 + 5, 60))
                break
        else:
            raise ValueError("No board found with id {}".format(board_id))


class ExpandingCircle(Circle):
    def __init__(self, center_x, center_y, final_radius):
        super().__init__(center_x, center_y, 0)
        self.final_radius = final_radius
        self.dead = False

    def step(self):
        if self.dead:
            return

        self.radius += 1
        if self.radius > self.final_radius:
            self.dead = True

    def draw(self, cairo_context):
        if self.dead:
            return

        cairo_context.arc(self.center_x, self.center_y, self.radius, 0, 2 * math.pi)
        cairo_context.set_line_width(1.5)
        cairo_context.set_source(
            cairo.SolidPattern(
                1, 1, 1,
                1 - self.radius / self.final_radius
            )
        )
        cairo_context.stroke()