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
        assert(self.hp > 0)
        self.hp -= 1
        if self.hp <= 0:
            self.state = Player.State.dead


class BoardElement:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def draw(self, context):
        raise NotImplementedError("Subclass must implement abstract method")


class Brick(BoardElement):
    def __init__(self, x, y, width, height, pattern):
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.pattern = pattern
        self.broken = False

    def draw(self, ctx):
        if not self.broken:
            ctx.set_line_width(1)
            ctx.set_source(self.pattern)
            ctx.rectangle(self.x+0.5, self.y+0.5, self.width-1, self.height-1)
            ctx.stroke()


class Ball(BoardElement):
    def __init__(self, x, y, speed, heading, pattern=cairo.SolidPattern(255, 0, 0), radius=1.5):
        super().__init__(x, y)
        self.speed = speed
        self.heading = heading
        self.pattern = pattern
        self.radius = radius
        #self.max_heading = *math.pi #maximum heading deviation from stright up/down motion

    def set_speed_x(self, x_speed):
        self.speed = (x_speed**2 + self.get_speed_y()**2)**0.5
        self.heading = math.atan2(self.get_speed_y(), x_speed)

    def set_speed_y(self, y_speed):
        self.speed = (y_speed**2 + self.get_speed_x()**2)**0.5
        self.heading = math.atan2(y_speed, self.get_speed_x())

    def modify_heading(self, delta):
        self.heading += delta
        #clamp(self.heading, self.max_heading, max_n)

    def get_speed_x(self):
        return self.speed*math.cos(self.heading)

    def get_speed_y(self):
        return self.speed*math.sin(self.heading)

    def step(self):
        #Make ball quicker
        self.speed += 0.001
        self.x += self.get_speed_x()
        self.y += self.get_speed_y()

    def draw(self, cairo_context):
        cairo_context.set_line_width(1)
        cairo_context.set_source(self.pattern)
        cairo_context.arc(self.x, self.y, self.radius, 0, 2*math.pi)
        cairo_context.stroke()


class Paddle(BoardElement):
    def __init__(self, x, y, width=24, height=4, speed=1, flipped=False):
        super().__init__(x, y)
        self.width = width
        self.height = height
        self.speed = speed
        self.flipped = flipped      # flips the paddle up/down
        self.gradient_pos = 0       # position of the gradient line on the paddle
        self.target_position = x    # Paddle will move towards it each step

    def set_health(self, health):
        health = max(0, health)
        self.gradient_pos = 1-health

    def set_position(self, position):
        self.set_target_position(position)
        self.x = position

    def set_target_position(self, target_position):
        self.target_position = target_position

    def step(self):
        #calculate difference between current and target position
        delta = self.target_position - self.x
        #move accordingly (limited by speed)
        self.x += clamp(delta, -self.speed, self.speed)

    def limit(self, limit):
        if self.x - self.width / 2 <= 0:
            self.x = self.width / 2

        if self.x + self.width / 2 >= limit+1:
            self.x = limit+1 - self.width / 2

    def draw(self, cr):
        cr.set_line_width(1)

        #Gradient background
        if self.flipped:
            pat = cairo.LinearGradient(self.x+self.width/2, 0.0, self.x-self.width/2-1, 0)
        else:
            pat = cairo.LinearGradient(self.x-self.width/2, 0.0, self.x+self.width/2+1, 0)
        pat.add_color_stop_rgb(self.gradient_pos, 0, 0, 1)
        pat.add_color_stop_rgb(self.gradient_pos, 0, 1, 0)
        cr.set_source(pat)

        x = self.x-self.width/2+self.height/2
        y = self.y+self.height/2
        r = self.height/2-0.5

        if self.flipped:
            y -= self.height-1

        cr.arc(x, y, r, math.pi/2, -math.pi/2)
        x = self.x+self.width/2-self.height/2
        cr.arc(x, y, r, -math.pi/2, math.pi/2)
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
        heading_delta = 0.1

        if paddle.flipped:
            collision_limit = paddle.y + ball.radius + 2
        else:
            collision_limit = paddle.y - ball.radius - 1

        if(
            (paddle.flipped     and ball.y <= collision_limit) or
            (not paddle.flipped and ball.y >= collision_limit)
        ):
            paddle_left_edge = paddle.x - paddle.width / 2
            paddle_right_edge = paddle.x + paddle.width / 2

            if paddle_left_edge <= ball.x <= paddle_right_edge:
                ball.y = collision_limit # Put ball back on the board

                direction = 1 if paddle.flipped else -1
                ball.set_speed_y(direction * abs(ball.get_speed_y()))

                if paddle_left_edge <= ball.x <= (paddle_left_edge + paddle.width/4):
                    ball.modify_heading(direction * heading_delta)

                elif (paddle_right_edge - paddle.width/4) <= ball.x <= paddle_right_edge:
                    ball.modify_heading(direction * -heading_delta)
