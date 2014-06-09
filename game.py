__author__ = 'Mark'


class Game:
    """
    Abstract class for a game
    Game has to implement at least these methods
    """
    def step(self):
        raise NotImplementedError("Subclass must implement abstract method")

    def draw(self, context):
        raise NotImplementedError("Subclass must implement abstract method")