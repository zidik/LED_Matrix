__author__ = 'Mark'

import random
import math
from threading import Thread

import game
from game_elements_library import Player, Paddle, Ball, delayed_function_call, collide_ball_to_paddle


class Pong(game.Game):
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
        self.reset_ball(self.p1)

    def test_ball_collisions(self):

        collide_ball_to_paddle(self.ball, self.p1_paddle)
        collide_ball_to_paddle(self.ball, self.p2_paddle)

        #Ball and wall
        if self.ball.x <= 0 + self.ball.radius:
            self.ball.set_speed_x(abs(self.ball.get_speed_x()))
            self.ball.x = -self.ball.x + 2*self.ball.radius

        if self.ball.x >= self.field_dims[0]-1 - self.ball.radius:
            self.ball.set_speed_x(-abs(self.ball.get_speed_x()))
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

    def reset_ball(self, loser=None):
        speed = 1
        heading = math.pi/2 + 0.15 * (random.randint(0, 1) * 2 - 1)

        if loser is None or loser == self.p1:
            y_dir = -1
        else:
            y_dir = 1

        self.ball = Ball(self.field_dims[0] / 2, self.field_dims[1] / 2, speed, y_dir * heading)

    def step(self):
        self.p1_paddle.step()
        self.p2_paddle.step()
        self.p1_paddle.limit(self.field_dims[1]-1)
        self.p2_paddle.limit(self.field_dims[1]-1)

        if self.ball is not None:
            self.ball.step()
            self.test_ball_collisions()

            loser = self.test_ball_outside()
            if loser:
                loser.lose_hp()
                if loser == self.p1:
                    self.p1_paddle.set_health((self.p1.hp-1) / (self.p1.max_hp-1))
                else:
                    self.p2_paddle.set_health((self.p2.hp-1) / (self.p2.max_hp-1))
                if loser.state == Player.State.alive:
                    self.ball = None
                    thread = Thread(target=delayed_function_call, args=(1, self.reset_ball, [loser]))
                    thread.start()
                else:
                    self.ball = None
                    thread = Thread(target=delayed_function_call, args=(5, self.reset_game))
                    thread.start()

    def draw(self, cairo_context):
        if self.ball is not None:
            self.ball.draw(cairo_context)
        self.p1_paddle.draw(cairo_context)
        self.p2_paddle.draw(cairo_context)