__author__ = 'Mark'

from enum import Enum
import time
import math

import cairo


class Player:
    class State(Enum):
        alive = 0
        dead = 1

    def __init__(self, max_hp=4):
        self.max_hp = max_hp
        self.hp = max_hp
        self.state = Player.State.alive

    def reset(self):
        self.hp = self.max_hp
        self.state = Player.State.alive

    def lose_hp(self):
        assert (self.hp > 0)
        self.hp -= 1
        if self.hp <= 0:
            self.state = Player.State.dead


class RectangleBoardElement():
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    @property
    def right(self):
        return self.left + self.width

    @right.setter
    def right(self, value):
        self.left = value - self.width

    @property
    def bottom(self):
        return self.top + self.height

    @bottom.setter
    def bottom(self, value):
        self.bottom = value - self.height

    @property
    def center_x(self):
        return self.left + self.width / 2

    @center_x.setter
    def center_x(self, value):
        self.left = value - self.width / 2

    @property
    def center_y(self):
        return self.top + self.height / 2

    @center_y.setter
    def center_y(self, value):
        self.top = value - self.height / 2


class CircleBoardElement():
    def __init__(self, center_x, center_y, radius):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius

    @property
    def left(self):
        return self.center_x - self.radius

    @left.setter
    def left(self, value):
        self.center_x = value + self.radius

    @property
    def right(self):
        return self.center_x + self.radius

    @right.setter
    def right(self, value):
        self.center_x = value - self.radius

    @property
    def top(self):
        return self.center_y - self.radius

    @top.setter
    def top(self, value):
        self.center_y = value + self.radius

    @property
    def bottom(self):
        return self.center_y + self.radius

    @bottom.setter
    def bottom(self, value):
        self.center_y = value - self.radius


class Brick(RectangleBoardElement):
    def __init__(self, x, y, width, height, pattern):
        super().__init__(x, y, width, height)
        self.pattern = pattern
        self.broken = False

    def draw(self, ctx):
        if not self.broken:
            ctx.set_line_width(1)
            ctx.set_source(self.pattern)
            ctx.rectangle(self.left + 0.5, self.top + 0.5, self.width - 1, self.height - 1)
            ctx.stroke()


class Ball(CircleBoardElement):
    def __init__(self, center_x, center_y, speed, heading, pattern=cairo.SolidPattern(255, 0, 0), radius=1.5):
        super().__init__(center_x, center_y, radius)
        self.speed = speed
        self.heading = heading
        self.pattern = pattern
        # self.max_heading = *math.pi #maximum heading deviation from straight up/down motion

    def set_speed_x(self, x_speed):
        self.speed = (x_speed ** 2 + self.get_speed_y() ** 2) ** 0.5
        self.heading = math.atan2(self.get_speed_y(), x_speed)

    def set_speed_y(self, y_speed):
        self.speed = (y_speed ** 2 + self.get_speed_x() ** 2) ** 0.5
        self.heading = math.atan2(y_speed, self.get_speed_x())

    def modify_heading(self, delta):
        self.heading += delta
        # clamp(self.heading, self.max_heading, max_n)

    def get_speed_x(self):
        return self.speed * math.cos(self.heading)

    def get_speed_y(self):
        return self.speed * math.sin(self.heading)

    def step(self):
        # Make ball quicker
        self.speed += 0.001
        self.center_x += self.get_speed_x()
        self.center_y += self.get_speed_y()

    def draw(self, cairo_context):
        cairo_context.set_line_width(1)
        cairo_context.set_source(self.pattern)
        cairo_context.arc(self.center_x, self.center_y, self.radius, 0, 2 * math.pi)
        cairo_context.stroke()


class Paddle(RectangleBoardElement):
    def __init__(self, left, top, width=24, height=4, speed=1, flipped=False):
        super().__init__(left, top, width, height)
        self.speed = speed
        self.flipped = flipped  # flips the paddle up/down
        self.gradient_pos = 0  # position of the gradient line on the paddle
        self.target_position = self.center_x  # Paddle will move towards it each step

    def set_health(self, health):
        health = max(0, health)
        self.gradient_pos = 1 - health

    def set_position(self, position):
        self.set_target_position(position)
        self.center_x = position

    def set_target_position(self, target_position):
        self.target_position = target_position

    def step(self):
        # calculate difference between current and target position
        delta = self.target_position - self.center_x
        #move accordingly (limited by speed)
        self.center_x += clamp(delta, -self.speed, self.speed)

    def limit(self, limit):
        if self.left <= 0:
            self.left = 0

        if self.right >= limit + 1:
            self.right = limit + 1

    def draw(self, cr):
        cr.set_line_width(1)

        # Gradient background
        if self.flipped:
            pat = cairo.LinearGradient(self.right, 0.0, self.left - 1, 0)
        else:
            pat = cairo.LinearGradient(self.left, 0.0, self.right + 1, 0)
        pat.add_color_stop_rgb(self.gradient_pos, 0, 0, 1)
        pat.add_color_stop_rgb(self.gradient_pos, 0, 1, 0)
        cr.set_source(pat)

        y = self.center_y
        r = self.height / 2 - 0.5
        x = self.left + self.height / 2
        cr.arc(x, y, r, math.pi / 2, -math.pi / 2)
        x = self.right - self.height / 2
        cr.arc(x, y, r, -math.pi / 2, math.pi / 2)
        cr.close_path()
        cr.stroke()


def clamp(n, min_n, max_n):
    return max(min(max_n, n), min_n)


def delayed_function_call(delay, function, args=None):
    time.sleep(delay)
    if args is None:
        function()
    else:
        function(*args)


def collide_ball_to_paddle(ball, paddle):
    assert(isinstance(paddle, Paddle))
    assert(isinstance(ball, Ball))
    heading_delta = 0.1  # change of heading of the ball on hitting edges of the paddle
    is_past_paddle = (paddle.flipped and ball.top < paddle.bottom) or (not paddle.flipped and ball.bottom > paddle.top)
    if is_past_paddle:
        if paddle.left <= ball.center_x <= paddle.right:
            #put ball back on the board
            if paddle.flipped:
                ball.top = paddle.bottom
            else:
                ball.bottom = paddle.top

            direction = 1 if paddle.flipped else -1
            ball.set_speed_y(direction * abs(ball.get_speed_y()))

            if paddle.left <= ball.center_x <= (paddle.left + paddle.width / 4):
                ball.modify_heading(direction * heading_delta)

            elif (paddle.right - paddle.width / 4) <= ball.center_x <= paddle.right:
                ball.modify_heading(direction * -heading_delta)
