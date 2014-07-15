__author__ = 'Mark'

import time
import math
from threading import Thread

import cairocffi as cairo


class Player:
    def __init__(self, max_hp=4):
        self.max_hp = max_hp
        self.hp = max_hp

    def reset(self):
        self.hp = self.max_hp

    def lose_hp(self):
        assert (self.hp > 0)
        self.hp -= 1

    @property
    def is_alive(self):
        return self.hp > 0


class Rectangle():
    def __init__(self, left, top, width, height):
        super().__init__()
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
        self.top = value - self.height

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

    def intersects(self, other):
        return not (
            self.bottom <= other.top or
            self.top >= other.bottom or
            self.left >= other.right or
            self.right <= other.left
        )

    def intersection(self, other):
        """
        :param other: Other rectangle
        :return: new rectangle with the size of the intersection
        if elements do not intersect - None
        """
        if self.intersects(other):
            left = max(self.left, other.left)
            right = min(self.right, other.right)
            bottom = min(self.bottom, other.bottom)
            top = max(self.top, other.top)
            width = right - left
            height = bottom - top
            return Rectangle(left, top, width, height)
        else:
            return None

    def union(self, other):
        """
        :param other: Other rectangle
        :return: new rectangle that completely covers both rectangles
        """
        left, top, width, height = self._union(other)
        return Rectangle(left, top, width, height)

    def union_ip(self, other):
        """
        Grows self so it covers the other rectangle too
        :param other: Other rectangle
        """
        self.left, self.top, self.width, self.height = self._union(other)

    def _union(self, other):
        left = min(self.left, other.left)
        right = max(self.right, other.right)
        bottom = max(self.bottom, other.bottom)
        top = min(self.top, other.top)
        width = right - left
        height = bottom - top
        return left, top, width, height


class Circle():
    def __init__(self, center_x, center_y, radius):
        super().__init__()
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


class Brick(Rectangle):
    def __init__(self, x, y, width, height, colors):
        super().__init__(x, y, width, height)
        self.patterns = []
        self.patterns.append(cairo.SolidPattern(*colors[0]))
        self.patterns.append(cairo.SolidPattern(*colors[1]))
        self.broken = False

    def draw(self, ctx):
        if not self.broken:
            ctx.rectangle(self.left + 0.5, self.top + 0.5, self.width - 1, self.height - 1)
            ctx.set_source(self.patterns[1])
            ctx.fill_preserve()
            ctx.set_source(self.patterns[0])
            ctx.set_line_width(1)
            ctx.stroke()


class Moving():
    def __init__(self):
        self.speed = 0
        self.heading = 0

    @property
    def speed_x(self):
        return self.speed * math.cos(self.heading)

    @speed_x.setter
    def speed_x(self, x_speed):
        self.speed = (x_speed ** 2 + self.speed_y ** 2) ** 0.5
        self.heading = math.atan2(self.speed_y, x_speed)

    @property
    def speed_y(self):
        return self.speed * math.sin(self.heading)

    @speed_y.setter
    def speed_y(self, y_speed):
        self.speed = (y_speed ** 2 + self.speed_x ** 2) ** 0.5
        self.heading = math.atan2(y_speed, self.speed_x)


class Ball(Circle, Moving):
    # Default values (prior loading config file)
    stroke_color = (0, 0, 1, 1)
    fill_color = (0, 0, 0, 1)
    radius = 1.5

    def __init__(self, center_x, center_y, speed, heading):
        super().__init__(center_x, center_y, Ball.radius)
        self.speed = speed
        self.heading = heading

        self.stroke_pattern = cairo.SolidPattern(*Ball.stroke_color)
        self.fill_pattern = cairo.SolidPattern(*Ball.fill_color)

    def step(self):
        last_bounding_box = Rectangle(self.left - 1, self.top - 1, 2 * self.radius + 2, 2 * self.radius + 2)

        self.center_x += self.speed_x
        self.center_y += self.speed_y

        new_bounding_box = Rectangle(self.left - 1, self.top - 1, 2 * self.radius + 2, 2 * self.radius + 2)
        dirty_area = last_bounding_box.union(new_bounding_box)
        return dirty_area

    def draw(self, cairo_context):
        cairo_context.arc(self.center_x, self.center_y, self.radius, 0, 2 * math.pi)
        cairo_context.set_line_width(1)
        cairo_context.set_source(self.fill_pattern)
        cairo_context.fill_preserve()
        cairo_context.set_source(self.stroke_pattern)
        cairo_context.stroke()


class Paddle(Rectangle):
    width = 24
    height = 4
    stroke_color = [(0, 1, 0, 1), (1, 0, 0, 1)]
    fill_color = [(0, 1, 0, 1), (1, 0, 0, 1)]

    def __init__(self, left, top, speed=1, flipped=False):
        super().__init__(left, top, Paddle.width, Paddle.height)
        self.speed = speed
        self.flipped = flipped  # flips the paddle up/down
        self.gradient_pos = 0  # position of the gradient line on the paddle
        self.target_position = self.center_x  # Paddle will move towards it each step
        self.invalidated_area = None  # area of canvas that Paddle thinks should be redrawn

    def set_health(self, health, max_health, blink=3):
        """
        Displays new health value on paddle
        :param health: new health value
        :param max_health: maximum health value
        :param blink: number of blinks to make to show change
        :raise ValueError: if health is lower than 0 or higher than "max_health"
        """
        if health < 0:
            raise ValueError("Health set less than 0")
        if health > max_health:
            raise ValueError("Health set more than maximum")

        health = max(0, health)
        self._blink_health(health, max_health, blink_count=blink)

    def _blink_health(self, health, max_health, blink_count=0, show_current=True):
        """
        Recursive function that blinks current and last health value on paddle
        :param health: current health value being shown
        :param max_health: maximum health value
        :param blink_count: number ob blinks left
        :param show_current: True if param "health" is current health value, otherwise it is previous
        """
        blink_period = 0.4
        if show_current:
            self.gradient_pos = 1 - (health - 1) / (max_health - 1)

            # Invalidate whole area so it will be redrawn
            self._invalidate_rect(Rectangle(self.left, self.top, self.width, self.height))

            if blink_count <= 0:
                return

            Thread(
                target=delayed_function_call,
                args=(blink_period / 2, self._blink_health, [health, max_health, blink_count - 1, False])
            ).start()
        else:
            self.gradient_pos = 1 - health / (max_health - 1)
            Thread(
                target=delayed_function_call,
                args=(blink_period / 2, self._blink_health, [health, max_health, blink_count])
            ).start()

    def set_position(self, position):
        self.set_target_position(position)
        self.center_x = position

    def set_target_position(self, target_position):
        self.target_position = target_position

    def step(self):
        # calculate difference between current and target position
        delta = self.target_position - self.center_x
        if abs(delta) > 0:
            last_bounding_box = Rectangle(self.left, self.top, self.width, self.height)
            # move accordingly (limited by speed)
            self.center_x += clamp(delta, -self.speed, self.speed)
            new_bounding_box = Rectangle(self.left, self.top, self.width, self.height)
            invalidated_area = last_bounding_box.union(new_bounding_box)
            self._invalidate_rect(invalidated_area)

    def _invalidate_rect(self, rect):
        if self.invalidated_area is None:
            self.invalidated_area = rect
        else:
            self.invalidated_area.union_ip(rect)

    def limit(self, limit):
        limited = False

        if self.left <= 0:
            self.left = 0
            limited = True

        if self.right >= limit + 1:
            self.right = limit + 1
            limited = True

        if limited:
            # Stop
            self.target_position = self.center_x

    def draw(self, cr):
        # Calculate Path
        y = self.center_y
        r = self.height / 2 - 0.5
        x = self.left + self.height / 2
        cr.arc(x, y, r, math.pi / 2, -math.pi / 2)
        x = self.right - self.height / 2
        cr.arc(x, y, r, -math.pi / 2, math.pi / 2)
        cr.close_path()

        #Fill
        # Gradient background
        if self.flipped:
            pat = cairo.LinearGradient(self.right + 1, 0.0, self.left - 1, 0)
        else:
            pat = cairo.LinearGradient(self.left - 1, 0.0, self.right + 1, 0)

        pat.add_color_stop_rgba(self.gradient_pos, *Paddle.fill_color[1])
        pat.add_color_stop_rgba(self.gradient_pos, *Paddle.fill_color[0])
        cr.set_source(pat)

        cr.fill_preserve()

        #Stroke
        if self.flipped:
            pat = cairo.LinearGradient(self.right + 1, 0.0, self.left - 1, 0)
        else:
            pat = cairo.LinearGradient(self.left - 1, 0.0, self.right + 1, 0)

        pat.add_color_stop_rgba(self.gradient_pos, *Paddle.stroke_color[1])
        pat.add_color_stop_rgba(self.gradient_pos, *Paddle.stroke_color[0])
        cr.set_source(pat)

        cr.set_line_width(1)
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
    assert (isinstance(paddle, Paddle))
    assert (isinstance(ball, Ball))
    heading_delta = 0.1  # change of heading of the ball on hitting edges of the paddle
    if paddle.intersection(ball):
        # put ball back on the board
        if paddle.flipped:
            ball.top = paddle.bottom
        else:
            ball.bottom = paddle.top

        direction = 1 if paddle.flipped else -1
        ball.speed_y = (direction * abs(ball.speed_y))

        if ball.center_x < (paddle.left + paddle.width / 4):
            ball.heading += direction * heading_delta

        elif (paddle.right - paddle.width / 4) < ball.center_x:
            ball.heading += direction * -heading_delta


def collide_to_left_wall(obj):
    if obj.left <= 0:
        obj.speed_x = abs(obj.speed_x)
        obj.left = 0 - obj.left


def collide_to_right_wall(obj, limit):
    if obj.right >= limit:
        obj.speed_x = -abs(obj.speed_x)
        obj.right = 2 * limit - obj.right


def collide_to_top_wall(obj):
    if obj.top <= 0:
        obj.speed_y = abs(obj.speed_y)
        obj.top = 0 - obj.top


def collide_to_bottom_wall(obj, limit):
    if obj.bottom >= limit:
        obj.speed_y = -abs(obj.speed_y)
        obj.bottom = 2 * limit - obj.bottom
