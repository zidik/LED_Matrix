__author__ = 'Mark'

import math
import random
from threading import Thread
from enum import Enum

# "Cairocffi" could be also installed as "cairo"
try:
    import cairocffi as cairo
except ImportError:
    import cairo

import game
from game_elements_library import Player, Paddle, Ball, Brick, delayed_function_call, \
    collide_ball_to_paddle, collide_to_left_wall, collide_to_right_wall, collide_to_top_wall, \
    are_colliding_rect_rect


class Breaker(game.Game):
    class State(Enum):
        starting_delay = 0
        waiting_push = 1
        running = 2
        finished = 3

    def __init__(self, field_dims):
        self.field_dims = field_dims

        self.player = Player()
        self.paddle = Paddle(0, self.field_dims[1] - 4)  # Paddle on the bottom
        self.balls = []
        self.bricks = []
        self._state = None
        self.ball_speed = None  # Speed set for all current balls

        self._reset_game()

    def button_pressed(self, button_number):
        """
        Signal the game that the button was pressed.

        :param button_number: number of the board-button pressed.
        """

        if not(0 <= button_number <= 9):
            raise ValueError("Invalid ButtonNumber")

        #Start the game if we were waiting for user
        if self._state == Breaker.State.waiting_push:
            self._state = Breaker.State.running

        self.paddle.set_target_position(10 / 2 + 10 * button_number)

    def step(self):
        if self._state != Breaker.State.running:
            return

        #Make game quicker
        self.paddle.speed += 0.001
        self.ball_speed += 0.001
        for ball in self.balls:
            ball.speed = self.ball_speed

        self.paddle.step()
        self.paddle.limit(self.field_dims[1] - 1)

        for ball in self.balls:
            ball.step()
            self._test_ball_collisions(ball)

            if self._is_ball_outside(ball):
                self.balls.remove(ball)

            if len(self.balls) == 0:
                self.player.lose_hp()
                self.paddle.set_health(self.player.hp, self.player.max_hp)
                if self.player.state == Player.State.alive:
                    Thread(target=delayed_function_call, args=(1, self._new_ball)).start()
                else:
                    self._state = Breaker.State.finished
                    Thread(target=delayed_function_call, args=(5, self._reset_game)).start()

        if self._state == Breaker.State.running and self._all_bricks_broken():
            self._state = Breaker.State.finished
            Thread(target=delayed_function_call, args=(1, self._reset_game)).start()

    def draw(self, ctx):
        for ball in self.balls:
            ball.draw(ctx)

        self.paddle.draw(ctx)
        for brick in self.bricks:
            brick.draw(ctx)

    def _reset_game(self):
        self._state = Breaker.State.starting_delay
        self.ball_speed = 1
        self.paddle.speed = 1
        self._reset_bricks()
        self.balls = []
        self.paddle.set_position((self.field_dims[0] - 1) / 2)
        self.paddle.set_health(self.player.max_hp, self.player.max_hp)
        self.player.reset()
        Thread(target=delayed_function_call, args=(2, self._start_waiting)).start()

    def _start_waiting(self):
        self._new_ball()
        self._state = Breaker.State.waiting_push

    def _test_ball_collisions(self, ball):
        collide_ball_to_paddle(ball, self.paddle)
        collide_to_left_wall(ball)
        collide_to_right_wall(ball, self.field_dims[0])
        collide_to_top_wall(ball)
        for brick in self.bricks:
            if not brick.broken:
                self._collide_ball_to_brick(ball, brick)

    def _collide_ball_to_brick(self, ball, brick):
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
                self._new_ball()  # add a ball with same speed

    def _is_ball_outside(self, ball):
        pixels_out = 1
        if ball.top > (self.field_dims[1] - 1) + pixels_out:
            return True
        return False

    def _new_ball(self):
        heading = math.pi / 2 + 0.15 * (random.randint(0, 1) * 2 - 1)
        ball = Ball(self.paddle.center_x, self.paddle.top, self.ball_speed, heading)
        ball.center_y -= ball.radius
        self.balls.append(ball)

    def _reset_bricks(self):
        distance_from_top = 15
        dims = 6, 4
        brick_dims = 14, 6
        patterns = cairo.SolidPattern(0, 0, 255), cairo.SolidPattern(0, 255, 255)
        for y in range(dims[1]):
            for x in range(dims[0]):
                self.bricks.append(
                    Brick(
                        x=(self.field_dims[0] - brick_dims[0] * dims[0]) / 2 + x * brick_dims[0],
                        y=distance_from_top + y * brick_dims[1],
                        width=brick_dims[0],
                        height=brick_dims[1],
                        pattern=patterns[(x + y) % 2]
                    )
                )

    def _all_bricks_broken(self):
        for brick in self.bricks:
            if not brick.broken:
                return False
        else:
            return True

