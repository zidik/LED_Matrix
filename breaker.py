__author__ = 'Mark'

import game
import math
import random
import cairo
from threading import Thread
from game_elements_library import Player, Paddle, Ball, Brick, delayed_function_call, collide_ball_to_paddle


class Breaker(game.Game):
    def __init__(self, field_dims):
        self.field_dims = field_dims
        self.player = Player()
        self.paddle = Paddle(0, self.field_dims[1]-4)    # Paddle on the bottom
        self.ball = None
        self.bricks = []
        self.reset_game()

    def reset_game(self):
        self.reset_bricks()
        self.paddle.set_position((self.field_dims[0]-1) / 2)
        self.paddle.set_health(1)
        self.player.reset()
        self.reset_ball()

    def test_ball_collisions(self):
        collide_ball_to_paddle(self.ball, self.paddle)

        #Ball and wall
        if self.ball.x <= 0 + self.ball.radius:
            self.ball.set_speed_x(abs(self.ball.get_speed_x()))
            self.ball.x = -self.ball.x + 2*self.ball.radius

        if self.ball.x >= self.field_dims[0]-1 - self.ball.radius:
            self.ball.set_speed_x(-abs(self.ball.get_speed_x()))
            self.ball.x = 2 * (self.field_dims[0]-1-self.ball.radius) - self.ball.x

        if self.ball.y <= 0 + self.ball.radius:
            self.ball.set_speed_y(abs(self.ball.get_speed_y()))
            self.ball.y = -self.ball.y + 2*self.ball.radius

    def test_ball_outside(self):
        if self.ball.y-self.ball.radius-1 > self.field_dims[1]-1:
            return True
        return False

    def reset_ball(self):
        speed = 1
        heading = math.pi/2 + 0.15 * (random.randint(0, 1) * 2 - 1)

        self.ball = Ball(self.paddle.x, self.paddle.y, speed, heading)

    def reset_bricks(self):
        dims = 6, 4
        brick_dims = 14, 6
        patterns = cairo.SolidPattern(0, 0, 255), cairo.SolidPattern(0, 255, 255)
        for y in range(dims[1]):
            for x in range(dims[0]):
                self.bricks.append(
                    Brick(
                        (self.field_dims[0]-brick_dims[0]*dims[0]) / 2 + x*brick_dims[0],
                        5 + y*brick_dims[1],
                        brick_dims[0],
                        brick_dims[1],
                        patterns[(x+y) % 2]
                    )
                )

    def step(self):
        self.paddle.step()
        self.paddle.limit(self.field_dims[1]-1)

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

