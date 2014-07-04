__author__ = 'Mark'

import math

# "Cairocffi" could be also installed as "cairo"
try:
    import cairocffi as cairo
except ImportError:
    import cairo

import game


class TestPattern(game.Game):
    def __init__(self, field_dims, board_assignments, board_buses):
        self.field_dims = field_dims
        self.board_assignments = board_assignments
        self.board_buses = board_buses

        self.connected_pat = cairo.LinearGradient(0.0, 0.0, 0.0, field_dims[1])
        for i in range(math.ceil(field_dims[1] / 10)):
            self.connected_pat.add_color_stop_rgba(i / 10, 0.0, 0.5
                                                   , 0.0, 1)
            self.connected_pat.add_color_stop_rgba((i + 1) / 10, 0, 0.2, 0, 1)

        self.disconnected_pat = cairo.LinearGradient(0.0, 0.0, 0.0, field_dims[1])
        for i in range(math.ceil(field_dims[1] / 10)):
            self.disconnected_pat.add_color_stop_rgba(i / 10, 0, 0, 0.8, 1)
            self.disconnected_pat.add_color_stop_rgba((i + 1) / 10, 0, 0, 0.4, 1)

        self.font_pat = cairo.SolidPattern(0.8, 0.8, 0.8, alpha=1.0)

    def step(self):
        pass

    def draw(self, ctx):
        font_options = ctx.get_font_options()
        font_options.set_antialias(cairo.ANTIALIAS_NONE)
        ctx.set_font_options(font_options)
        ctx.set_font_size(9)  # em-square height is 90 pixels

        for board_id, col, row in self.board_assignments:
            ctx.set_source(self.disconnected_pat)
            ctx.rectangle(10 * col, 10 * row, 10 * (col + 1), 10 * (row + 1))
            ctx.fill()

            # ctx.set_source_rgba(0, 0, 0, 1)
            # ctx.stroke()

            ctx.move_to(10 * col, 10 * row + 8)
            ctx.set_source(self.font_pat)
            ctx.show_text("%x" % board_id)

        for bus in self.board_buses:
            for board in bus.boards:
                ctx.set_source(self.connected_pat)
                ctx.rectangle(10 * board.column, 10 * board.row, 10 * (board.column + 1), 10 * (board.row + 1))
                ctx.fill()

                # ctx.set_source_rgba(0, 0, 0, 1)
                #ctx.stroke()

                ctx.move_to(10 * board.column, 10 * board.row + 8)
                ctx.set_source(self.font_pat)
                ctx.show_text("%x" % board.id)



