__author__ = 'Mark'

import random

from enum import Enum
import time
import cairo
import math
from threading import Thread



P1 = 1
P2 = 2


def delayed_function_call(delay, function, args=None):
    time.sleep(delay)
    if args is None:
        function()
    else:
        function(*args)


class Pong:
    def __init__(self, field_dims):

        self.field_dims = field_dims

        self.p1 = Player()
        self.p2 = Player()

        self.p1_paddle = Paddle(0, self.field_dims[1]-4)    # Paddle on the bottom
        self.p2_paddle = Paddle(0, 3, flipped=True)         # Paddle on the top

        self.ball = None

        self.reset_game()

    def reset_game(self):
        self.reset_paddles()
        self.p1.reset()
        self.p2.reset()
        self.reset_ball()




    #TODO: Currently ball must not move faster than paddle thickness
    def test_ball_collisions(self):
        #ball is behind p2 paddle
        if self.ball.y <= self.p2_paddle.y + self.ball.radius +2:  # Behind the front of the paddle
            paddle_left_edge = self.p2_paddle.x - self.p2_paddle.width / 2
            paddle_right_edge = self.p2_paddle.x + self.p2_paddle.width / 2

            if paddle_left_edge <= self.ball.x <= paddle_right_edge:
                self.ball.y_speed = abs(self.ball.y_speed)
                #self.ball.y = 2 * (-self.p2_paddle.y + self.ball.radius) - self.ball.y

        #ball is behind p1 paddle
        if self.ball.y >= self.p1_paddle.y - self.ball.radius -1:
            paddle_left_edge = self.p1_paddle.x - self.p1_paddle.width / 2
            paddle_right_edge = self.p1_paddle.x + self.p1_paddle.width / 2

            if paddle_left_edge <= self.ball.x <= paddle_right_edge:
                self.ball.y_speed = -abs(self.ball.y_speed)
                #self.ball.y = 2 * (self.p1_paddle.y-self.ball.radius) - self.ball.y

        #Ball and wall
        if self.ball.x <= 0 + self.ball.radius:
            self.ball.x_speed = abs(self.ball.x_speed)
            self.ball.x = -self.ball.x + 2*self.ball.radius

        if self.ball.x >= self.field_dims[0]-1 - self.ball.radius:
            self.ball.x_speed = -abs(self.ball.x_speed)
            self.ball.x = 2 * (self.field_dims[0]-1-self.ball.radius) - self.ball.x

    def test_ball_outside(self):
        if self.ball.y+self.ball.radius+1 < 0:
            return self.p2
        if self.ball.y-self.ball.radius-1 > self.field_dims[1]-1:
            return self.p1
        return False

    def reset_paddles(self):
        self.p1_paddle.set_position((self.field_dims[0]-1) / 2)
        self.p2_paddle.set_position((self.field_dims[0]-1) / 2)
        self.p1_paddle.set_health(1)
        self.p2_paddle.set_health(1)

    def reset_ball(self, loser=P1):
        x_speed = 0.2
        y_speed = 1.0

        x_dir = (random.randint(0, 1) * 2 - 1)
        if loser == P1:
            y_dir = -1
        else:
            y_dir = 1

        self.ball = Ball(self.field_dims[0] / 2, self.field_dims[1] / 2, x_dir * x_speed, y_dir * y_speed)

    def step(self):
        if self.ball is not None:
            self.ball.step()
            self.test_ball_collisions()

            loser = self.test_ball_outside()
            if loser:
                loser.lose_hp()
                if loser == self.p1:
                    self.p1_paddle.set_health(self.p1.hp / self.p1.max_hp)
                else:
                    self.p2_paddle.set_health(self.p2.hp / self.p2.max_hp)
                if loser.state == Player.State.alive:
                    self.ball = None
                    thread = Thread(target=delayed_function_call, args=(1, self.reset_ball, [loser]))
                    thread.start()
                else:
                    self.ball = None
                    thread = Thread(target=delayed_function_call, args=(5, self.reset_game))
                    thread.start()


        self.p1_paddle.step()
        self.p2_paddle.step()
        self.p1_paddle.limit(self.field_dims[1]-1)
        self.p2_paddle.limit(self.field_dims[1]-1)

    def draw(self, cairo_context):
        if self.ball is not None:
            self.ball.draw(cairo_context)
        self.p1_paddle.draw(cairo_context)
        self.p2_paddle.draw(cairo_context)


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


class Ball:
    def __init__(self, x, y, x_speed, y_speed, pattern=cairo.SolidPattern(255, 0, 0), radius=1.5):
        self.x = x
        self.y = y
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.pattern = pattern
        self.radius = radius

    def step(self, size=1):
        self.x += self.x_speed * size
        self.y += self.y_speed * size

    def draw(self, cairo_context):
        cairo_context.set_line_width(1)
        cairo_context.set_source(self.pattern)
        cairo_context.arc(self.x, self.y, self.radius, 0, 2*math.pi)
        cairo_context.stroke()


class Paddle:
    def __init__(self, x, y, width=24, height=4, speed=1, flipped=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = speed
        self.flipped = flipped      # flips the paddle up/down
        self.gradient_pos = 0       # position of the gradient line on the paddle
        self.target_position = x    # Paddle will move towards it each step

    def set_health(self, health):
        assert(0 <= health <= 1)
        self.gradient_pos = 1-health

    def set_position(self, position):
        self.set_target_position(position)
        self.x = position

    def set_target_position(self, target_position):
        self.target_position = target_position

    def step(self):

        def clamp(n, min_n, max_n):
            return max(min(max_n, n), min_n)

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


