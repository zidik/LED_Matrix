__author__ = 'Mark'

LEFT = 1
RIGHT = 2

P1 = 1
P2 = 2

class Ball:
    def __init__(self, x, y, x_speed, y_speed):
        self.x = x
        self.y = y
        self.x_speed = x_speed
        self.y_speed = y_speed

    def step(self, size=1):
        self.x += self.x_speed*size
        self.y += self.y_speed*size
        self.limit()

    def limit(self):
        #BOUNCE
        if self.x <= 0:
            self.x_speed = abs(self.x_speed)
            self.x = -self.x
        if self.y <= 0:
            self.y_speed = abs(self.y_speed)
            self.y = -self.y

        limit = 19
        if self.x >= limit:
            self.x_speed = -abs(self.x_speed)
            self.x = 2*limit - self.x
        if self.y >= limit:
            self.y_speed = -abs(self.y_speed)
            self.y = 2*limit - self.y


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



