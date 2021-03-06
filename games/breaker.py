from games import game

__author__ = 'Mark'

import math
import random
from threading import Thread
from enum import Enum, unique

import cairocffi as cairo

from games.game_elements_library import Rectangle, Player, Paddle, Ball, Brick, delayed_function_call, \
    collide_ball_to_paddle, collide_to_left_wall, collide_to_right_wall, collide_to_top_wall


class Breaker(game.Game):
    brick_colors = [
        [(1, 1, 1, 1), (1, 1, 1, 1)],
        [(0.5, 0.5, 0.5, 1), (0.5, 0.5, 0.5, 1)]
    ]
    brick_columns = 6
    brick_rows = 4

    init_ball_speed = 1.0
    init_paddle_speed = 1.0
    speed_change = 0.001

    lives = 4

    multi_ball_probability = 0.1

    @unique
    class State(Enum):
        initialising = -1
        starting_delay = 0
        waiting_push = 1
        running = 2
        finished = 3

    def __init__(self, field_dims):
        self.field_dims = field_dims

        self._state = Breaker.State.initialising
        self.invalidated_areas = []
        self.player = Player(Breaker.lives)
        self.paddle = Paddle(0, self.field_dims[1] - 4, speed=Breaker.init_paddle_speed)  # Paddle on the bottom
        self.balls = []
        self.bricks = []
        self.ball_speed = Breaker.init_ball_speed  # Speed set for all current balls

        self._reset_game()

    def button_pressed(self, button_number):
        """
        Signal the game that the button was pressed.

        :param button_number: number of the board-button pressed.
        """

        if not (0 <= button_number <= 9):
            raise ValueError("Invalid ButtonNumber")

        # Start the game if we were waiting for user
        if self._state == Breaker.State.waiting_push:
            self._state = Breaker.State.running

        self.paddle.set_target_position(10 / 2 + 10 * button_number)

    def step(self):
        if self._state != Breaker.State.running:
            return

        # Make game quicker
        self.paddle.speed += Breaker.speed_change
        self.ball_speed += Breaker.speed_change
        for ball in self.balls:
            ball.speed = self.ball_speed

        self.paddle.step()

        self.paddle.limit(self.field_dims[1] - 1)

        for ball in self.balls:
            dirty_area_ball = ball.step()
            self.invalidated_areas.append(dirty_area_ball)

            self._test_ball_collisions(ball)

            if self._is_ball_outside(ball):
                self.balls.remove(ball)

            if len(self.balls) == 0:
                self.player.lose_hp()
                self.paddle.set_health(self.player.hp, self.player.max_hp)
                if self.player.is_alive:
                    Thread(target=delayed_function_call, args=(1, self._new_ball)).start()
                else:
                    self._state = Breaker.State.finished
                    Thread(target=delayed_function_call, args=(5, self._reset_game)).start()

        if self._state == Breaker.State.running and self._all_bricks_broken():
            self._state = Breaker.State.finished
            Thread(target=delayed_function_call, args=(1, self._reset_game)).start()

    def draw(self, ctx):
        if self.paddle.invalidated_area is not None:
            self.invalidated_areas.append(self.paddle.invalidated_area)
            self.paddle.invalidated_area = None

        for invalidated_area in self.invalidated_areas:
            self._draw(ctx, invalidated_area)
        self.invalidated_areas = []

    def _draw(self, ctx, invalidated_rect):
        # ## DEBUG OPTIONS ###
        display_redraw = False
        # ####################

        not_redrawn = self.balls + [self.paddle] + self.bricks  # Elements that will not be redrawn
        redrawn = []  # Elements that will be redrawn

        # Add all elements that reside inside "invalidated rect" to list "redrawn"
        new_added = True
        while new_added:
            new_added = False
            for element in not_redrawn:
                if invalidated_rect.intersection(element):
                    not_redrawn.remove(element)
                    redrawn.append(element)
                    invalidated_rect.union_ip(element)  # Grow invalidated rect
                    new_added = True  # invalidated_rect in now bigger, we have to check all again
                    break

        ctx.rectangle(
            int(invalidated_rect.left),
            int(invalidated_rect.top),
            math.ceil(invalidated_rect.width + (invalidated_rect.left - int(invalidated_rect.left))),
            math.ceil(invalidated_rect.height + (invalidated_rect.top - int(invalidated_rect.top)))
        )

        # show redrawn area
        if display_redraw:
            pat = cairo.SolidPattern(1.0, 0.0, 0.0, 0.5)
            ctx.set_source(pat)
            ctx.stroke_preserve()

        # Clear area inside area being redrawn
        ctx.set_source_rgb(0, 0, 0)
        ctx.fill()

        # Redraw all elements, that are inside this area
        for element in redrawn:
            element.draw(ctx)

    def _reset_game(self):
        self._state = Breaker.State.starting_delay
        self.ball_speed = 1
        self.paddle.speed = 1
        self._reset_bricks()
        self.balls = []
        self.paddle.set_position((self.field_dims[0] - 1) / 2)
        self.paddle.set_health(self.player.max_hp, self.player.max_hp, blink=0)
        self.player.reset()
        Thread(target=delayed_function_call, args=(2, self._start_waiting)).start()
        self.invalidated_areas = [Rectangle(0, 0, self.field_dims[0], self.field_dims[1])]

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
        intersection = brick.intersection(ball)
        if intersection is not None:
            if intersection.width > intersection.height:
                # bounce from top-or bottom
                ball.speed_y = math.copysign(
                    ball.speed_y,
                    ball.center_y - brick.center_y
                )
            else:
                # bounce from sides
                ball.speed_x = math.copysign(
                    ball.speed_x,
                    ball.center_x - brick.center_x
                )

            self.bricks.remove(brick)
            if random.random() < Breaker.multi_ball_probability:
                self._new_ball()  # add a ball with same speed
            self.invalidated_areas.append(brick)

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
        self.invalidated_areas.append(ball.bounding_box)

    def _reset_bricks(self):
        self.bricks = []
        distance_from_top = 15
        brick_dims = 14, 6
        for y in range(Breaker.brick_rows):
            for x in range(Breaker.brick_columns):
                self.bricks.append(
                    Brick(
                        x=(self.field_dims[0] - brick_dims[0] * Breaker.brick_columns) / 2 + x * brick_dims[0],
                        y=distance_from_top + y * brick_dims[1],
                        width=brick_dims[0],
                        height=brick_dims[1],
                        colors=Breaker.brick_colors[(x + y) % 2]
                    )
                )

    def _all_bricks_broken(self):
        for brick in self.bricks:
            if not brick.broken:
                return False
        else:
            return True