__author__ = 'Mark'

import numpy

LEFT = 1
RIGHT = 2

P1 = 1
P2 = 2

class Pong:
    def __init__(self, buttons):
        self.p1_left_button, self.p1_right_button, self.p2_left_button, self.p2_right_button = buttons

        self.field_dims = 19, 19
        self.ball = None
        self.p1_paddle = None  #Paddle on the bottom
        self.p2_paddle = None     #Paddle on the top

        self.reset_ball()
        self.reset_paddles()

    #TODO: Currently ball must not move faster than paddle thickness
    def test_ball_collisions(self):
        #ball is behind p2 paddle
        if self.ball.y <= self.p2_paddle.y+1:
            print("Paddle")
            paddle_left_edge = self.p2_paddle.x-self.p2_paddle.size/2
            paddle_right_edge = self.p2_paddle.x+self.p2_paddle.size/2

            if paddle_left_edge <= self.ball.x <= paddle_right_edge:
                self.ball.y_speed = abs(self.ball.y_speed)
                self.ball.y = 2 * (self.p2_paddle.y + 1) - self.ball.y

        #ball is behind p1 paddle
        if self.ball.y >= self.p1_paddle.y:
            paddle_left_edge = self.p1_paddle.x-self.p1_paddle.size/2
            paddle_right_edge = self.p1_paddle.x+self.p1_paddle.size/2

            if paddle_left_edge <= self.ball.x <= paddle_right_edge:
                self.ball.y_speed = -abs(self.ball.y_speed)
                self.ball.y = 2 * (self.p1_paddle.y) - self.ball.y

        #Ball and wall
        if self.ball.y <= 0:
            self.ball.y_speed = abs(self.ball.y_speed)
            self.ball.y = -self.ball.y

        if self.ball.y >= self.field_dims[1]:
            self.ball.y_speed = -abs(self.ball.y_speed)
            self.ball.y = 2*self.field_dims[1] - self.ball.y

    def reset_paddles(self):
        self.p1_paddle = Paddle(self.field_dims[0]/2, self.field_dims[1], 5)
        self.p2_paddle = Paddle(self.field_dims[0]/2, 0, 5)

    def reset_ball(self):
        self.ball = Ball(self.field_dims[0]/2, self.field_dims[1]/2, 0.2, -1)

    def step(self):
        self.ball.step()
        self.test_ball_collisions()
        if self.p1_left_button.is_pressed():
            self.p1_paddle.move(LEFT)
        if self.p1_right_button.is_pressed():
            self.p1_paddle.move(RIGHT)
        if self.p2_left_button.is_pressed():
            self.p2_paddle.move(LEFT)
        if self.p2_right_button.is_pressed():
            self.p2_paddle.move(RIGHT)

    def draw(self, image_buffer):
        self.ball.draw(image_buffer)
        self.p1_paddle.draw(image_buffer)
        self.p2_paddle.draw(image_buffer)




class Ball:
    def __init__(self, x, y, x_speed, y_speed):
        self.x = x
        self.y = y
        self.x_speed = x_speed
        self.y_speed = y_speed

    def step(self, size=1):
        self.x += self.x_speed*size
        self.y += self.y_speed*size

    def draw(self, image_buffer):
        image_buffer[round(self.y), round(self.x)] = numpy.array([3*[255]])


class Paddle:
    def __init__(self, x, y, size, speed=1):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed

    def move(self, side):
        if side == LEFT:
            self.x += self.speed
        elif side == RIGHT:
            self.x -= self.speed
        else:
            raise ValueError("Invalid side")
        self.limit()

    def limit(self):
        if self.x - self.size <= 0:
            self.x = self.size

        limit = 19
        if self.x + self.size >= limit:
            self.x = limit - self.size

    def draw(self, image_buffer):
        image_buffer[
            round(self.y),
            round(self.x-self.size/2):round(self.x+self.size/2)+1
        ] = numpy.array([255, 255, 255])



