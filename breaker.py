__author__ = 'Mark'

import math
import random
from threading import Thread

import cairo

import game
from game_elements_library import Player, Paddle, Ball, Brick, delayed_function_call,\
    collide_ball_to_paddle, collide_ball_to_left_wall, collide_ball_to_right_wall, collide_ball_to_top_wall,\
    are_colliding_rect_rect


class Breaker(game.Game):
    def __init__(self, field_dims):
        self.field_dims = field_dims
        self.player = Player()
        self.paddle = Paddle(0, self.field_dims[1] - 4)  # Paddle on the bottom
        self.ball = None
        self.bricks = []
        self.reset_game()

    def reset_game(self):
        self.reset_bricks()
        self.paddle.set_position((self.field_dims[0] - 1) / 2)
        self.paddle.set_health(1)
        self.player.reset()
        self.reset_ball()

    def test_ball_collisions(self):
        collide_ball_to_paddle(self.ball, self.paddle)

        collide_ball_to_left_wall(self.ball)
        collide_ball_to_right_wall(self.ball, self.field_dims[0])
        collide_ball_to_top_wall(self.ball)

        self.collide_ball_to_bricks()

    def collide_ball_to_bricks(self):
        for brick in self.bricks:
            if not brick.broken:
                if are_colliding_rect_rect(self.ball, brick):
                    brick.broken = True

    def test_ball_outside(self):
        pixels_out = 1
        if self.ball.top > (self.field_dims[1] - 1) + pixels_out:
            return True
        return False

    def reset_ball(self):
        speed = 1
        heading = math.pi / 2 + 0.15 * (random.randint(0, 1) * 2 - 1)

        self.ball = Ball(self.paddle.center_x, self.paddle.center_y, speed, heading)

    def reset_bricks(self):
        dims = 6, 4
        brick_dims = 14, 6
        patterns = cairo.SolidPattern(0, 0, 255), cairo.SolidPattern(0, 255, 255)
        for y in range(dims[1]):
            for x in range(dims[0]):
                self.bricks.append(
                    Brick(
                        (self.field_dims[0] - brick_dims[0] * dims[0]) / 2 + x * brick_dims[0],
                        5 + y * brick_dims[1],
                        brick_dims[0],
                        brick_dims[1],
                        patterns[(x + y) % 2]
                    )
                )

    def step(self):
        self.paddle.step()
        self.paddle.limit(self.field_dims[1] - 1)

        if self.ball is not None:
            self.ball.step()
            self.test_ball_collisions()

            if self.test_ball_outside():
                self.player.lose_hp()
                self.paddle.set_health(self.player.hp / self.player.max_hp)
                if self.player.state == Player.State.alive:
                    self.ball = None
                    thread = Thread(target=delayed_function_call, args=(1, self.reset_ball))
                    thread.start()
                else:
                    self.ball = None
                    thread = Thread(target=delayed_function_call, args=(5, self.reset_game))
                    thread.start()

    def draw(self, ctx):
        if self.ball is not None:
            self.ball.draw(ctx)
        self.paddle.draw(ctx)
        for brick in self.bricks:
            brick.draw(ctx)

