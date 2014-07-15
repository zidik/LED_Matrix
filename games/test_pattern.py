__author__ = 'Mark'

import cairocffi as cairo

from games import game


class TestPattern(game.Game):
    def __init__(self, matrix_dims, board_assignments, board_buses):
        self.board_assignments = board_assignments
        self.board_buses = board_buses

        self.connected_pat = cairo.LinearGradient(0.0, 0.0, 0.0, matrix_dims[1]*10)
        for i in range(matrix_dims[1]):
            self.connected_pat.add_color_stop_rgba(i / matrix_dims[1], 0.0, 0.5
                                                   , 0.0, 1)
            self.connected_pat.add_color_stop_rgba((i + 1) / matrix_dims[1], 0, 0.2, 0, 1)

        self.disconnected_pat = cairo.LinearGradient(0.0, 0.0, 0.0, matrix_dims[1]*10)
        for i in range(matrix_dims[1]):
            self.disconnected_pat.add_color_stop_rgba(i / matrix_dims[1], 0, 0, 0.8, 1)
            self.disconnected_pat.add_color_stop_rgba((i + 1) / matrix_dims[1], 0, 0, 0.4, 1)

        self.font_pat = cairo.SolidPattern(0.8, 0.8, 0.8, alpha=1.0)

    def step(self):
        pass

    def draw(self, ctx):
        #Clear
        ctx.set_source_rgb(0, 0, 0)
        ctx.paint()

        font_options = ctx.get_font_options()
        font_options.set_antialias(cairo.ANTIALIAS_NONE)
        ctx.set_font_options(font_options)
        ctx.set_font_size(9)  # em-square height is 90 pixels

        # Paint all board assignments with "disconnected" pattern
        ctx.set_source(self.disconnected_pat)
        for board_id, col, row in self.board_assignments:
            ctx.rectangle(10 * col, 10 * row, 10 * (col + 1), 10 * (row + 1))
            ctx.fill()

            # ctx.set_source_rgba(0, 0, 0, 1)
            # ctx.stroke()

        # Repaint all connected boards with "connected" pattern
        for bus in self.board_buses:
            for board in bus.boards:
                ctx.set_source(self.connected_pat)
                ctx.rectangle(10 * board.column, 10 * board.row, 10, 10)
                ctx.fill()

        #Display edges of a board
        stroke = False
        if stroke:
            ctx.set_source_rgba(0, 0, 0, 1)
            for board_id, col, row in self.board_assignments:
                ctx.rectangle(10 * col + 0.5, 10 * row + 0.5, 9, 9)
                ctx.stroke()

        #Display board-id's on respective boards
        ctx.set_source(self.font_pat)
        for board_id, col, row in self.board_assignments:
            ctx.move_to(10 * col, 10 * row + 8)
            ctx.show_text("%x" % board_id)



