__author__ = 'Mark'

import math
import random
from threading import Thread

# "Cairocffi" could be also installed as "cairo"
try:
    import cairocffi as cairo
except ImportError:
    import cairo

import game
from game_elements_library import Player, Paddle, Ball, Brick, delayed_function_call, \
    collide_ball_to_paddle, collide_ball_to_left_wall, collide_ball_to_right_wall, collide_ball_to_top_wall, \
    are_colliding_rect_rect


class Breaker(game.Game):
    def __init__(self, field_dims):
        self.field_dims = field_dims
        self.player = Player()
        self.paddle = Paddle(0, self.field_dims[1] - 4)  # Paddle on the bottom
        self.balls = []
        self.bricks = []
        self.reset_game()

    def reset_game(self):
        self.reset_bricks()
        self.paddle.set_position((self.field_dims[0] - 1) / 2)
        self.paddle.set_health(1)
        self.player.reset()
        self.new_ball()

    def test_ball_collisions(self, ball):
        collide_ball_to_paddle(ball, self.paddle)
        collide_ball_to_left_wall(ball)
        collide_ball_to_right_wall(ball, self.field_dims[0])
        collide_ball_to_top_wall(ball)
        for brick in self.bricks:
            if not brick.broken:
                self.collide_ball_to_brick(ball, brick)

    def collide_ball_to_brick(self, ball, brick):
        if are_colliding_rect_rect(ball, brick):
            intersection = brick.intersection(ball)
            if intersection.width > intersection.height:
                #bounce from top-or bottom
                ball.speed_y = math.copysign(
                    ball.speed_y,
                    ball.center_y - brick.center_y
                )
            else:
                #bounce from sides
                ball.speed_x = math.copysign(
                    ball.speed_x,
                    ball.center_x - brick.center_x
                )

            brick.broken = True
            probability = 0.1
            if random.random() < probability:
                self.new_ball(ball.speed)  # add a ball with same speed

    def is_ball_outside(self, ball):
        pixels_out = 1
        if ball.top > (self.field_dims[1] - 1) + pixels_out:
            return True
        return False

    def new_ball(self, speed=1):
        heading = math.pi / 2 + 0.15 * (random.randint(0, 1) * 2 - 1)
        self.balls.append(Ball(self.paddle.center_x, self.paddle.center_y, speed, heading))

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

        for ball in self.balls:
            ball.step()
            self.test_ball_collisions(ball)

            if self.is_ball_outside(ball):
                self.balls.remove(ball)

            if len(self.balls) == 0:
                self.player.lose_hp()
                self.paddle.set_health(self.player.hp / self.player.max_hp)
                if self.player.state == Player.State.alive:
                    Thread(target=delayed_function_call, args=(1, self.new_ball)).start()
                else:
                    Thread(target=delayed_function_call, args=(5, self.reset_game)).start()

        if self.all_bricks_broken():
            pass
            #TODO:
            #Thread(target=delayed_function_call, args=(1, self.reset_game)).start()

    def draw(self, ctx):
        for ball in self.balls:
            ball.draw(ctx)

        self.paddle.draw(ctx)
        for brick in self.bricks:
            brick.draw(ctx)

    def all_bricks_broken(self):
        for brick in self.bricks:
            if not brick.broken:
                return False
        else:
            return True

