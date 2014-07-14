__author__ = 'Mark'

import random
import math
from threading import Thread
from enum import Enum

import game
from game_elements_library import Player, Paddle, Ball, delayed_function_call, \
    collide_ball_to_paddle, collide_to_left_wall, collide_to_right_wall


class Pong(game.Game):

    lives = 4

    init_ball_speed = 0.1
    init_paddle_speed = 0.1
    speed_change = 0.001

    class State(Enum):
        starting_delay = 0
        waiting_push = 1
        running = 2
        finished = 3

    def __init__(self, field_dims):
        self._field_dims = field_dims

        self._p1 = Player(Pong.lives)
        self._p2 = Player(Pong.lives)

        self._p1_paddle = Paddle(0, self._field_dims[1] - 4, speed=Pong.init_paddle_speed)  # Paddle on the bottom
        self._p2_paddle = Paddle(0, 0, flipped=True, speed=Pong.init_paddle_speed)  # Paddle on the top

        self.ball_speed = 1

        self._ball = None
        self._state = None
        self._reset_game()

    def button_pressed(self, player, button_number):
        """
        Signal the game that the button was pressed.

        :param player: number of the player
        :param button_number: number of the board-button pressed.
        """
        if player == 1:
            paddle = self._p1_paddle
        elif player == 2:
            paddle = self._p2_paddle
        else:
            raise ValueError("Invalid Player")

        if not(0 <= button_number <= 9):
            raise ValueError("Invalid ButtonNumber")

        #Start the game if we were waiting for user
        if self._state == Pong.State.waiting_push:
            self._state = Pong.State.running

        paddle.set_target_position(10 / 2 + 10 * button_number)

    def step(self):
        if not (self._state == Pong.State.running):
            return

        #Make game quicker
        self._p1_paddle.speed += Pong.speed_change
        self._p2_paddle.speed += Pong.speed_change
        self.ball_speed += Pong.speed_change

        self._p1_paddle.step()
        self._p2_paddle.step()
        self._p1_paddle.limit(self._field_dims[1] - 1)
        self._p2_paddle.limit(self._field_dims[1] - 1)

        if self._ball is not None:
            self._ball.step()
            self._ball.speed = self.ball_speed
            self._test_ball_collisions()

            loser = self._test_ball_outside()
            if loser:
                loser.lose_hp()
                if loser == self._p1:
                    self._p1_paddle.set_health(self._p1.hp, self._p1.max_hp)
                else:
                    self._p2_paddle.set_health(self._p2.hp, self._p2.max_hp)
                if loser.is_alive:
                    self._ball = None
                    #reduce ball speed 1/3'rd
                    #self.ball_speed = self.ball_speed/3*2
                    thread = Thread(target=delayed_function_call, args=(1, self._reset_ball, [loser]))
                    thread.start()
                else:
                    self._ball = None
                    self._state = Pong.State.finished
                    thread = Thread(target=delayed_function_call, args=(5, self._reset_game))
                    thread.start()

    def draw(self, cairo_context):
        if self._ball is not None:
            self._ball.draw(cairo_context)
        self._p1_paddle.draw(cairo_context)
        self._p2_paddle.draw(cairo_context)

    def _reset_game(self):
        self._state = Pong.State.starting_delay
        self.ball_speed = 1
        self._reset_paddles()
        self._p1.reset()
        self._p2.reset()
        Thread(target=delayed_function_call, args=(2, self._start_waiting)).start()

    def _start_waiting(self):
        self._reset_ball(random.choice([self._p1, self._p2]))
        self._state = Pong.State.waiting_push


    def _test_ball_collisions(self):

        collide_ball_to_paddle(self._ball, self._p1_paddle)
        collide_ball_to_paddle(self._ball, self._p2_paddle)

        collide_to_left_wall(self._ball)
        collide_to_right_wall(self._ball, self._field_dims[0])

    def _test_ball_outside(self):
        pixels_out = 1
        if self._ball.bottom < 0 - pixels_out:
            return self._p2
        if self._ball.top > (self._field_dims[1] - 1) + pixels_out:
            return self._p1
        return False

    def _reset_paddles(self):
        self._p1_paddle.set_position((self._field_dims[0] - 1) / 2)
        self._p2_paddle.set_position((self._field_dims[0] - 1) / 2)
        self._p1_paddle.speed = 1
        self._p2_paddle.speed = 1
        self._p1_paddle.set_health(self._p1.max_hp, self._p1.max_hp)
        self._p2_paddle.set_health(self._p1.max_hp, self._p1.max_hp)

    def _reset_ball(self, loser=None):
        heading = math.pi / 2 + 0.15 * random.choice([1, -1])

        if loser is None or loser == self._p1:
            y_dir = -1
        else:
            y_dir = 1

        self._ball = Ball(self._field_dims[0] / 2, self._field_dims[1] / 2, self.ball_speed, y_dir * heading)