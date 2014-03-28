__author__ = 'Mark Laane'
import time
import logging


def running_led(boards, cycles=4, color=[3, 3, 3], debug_info = False):
    for i in range(cycles * 100):
        input_list = test_list_generator(i % 100, color)
        t1 = time.time()
        for board in boards:
            board.refresh_leds(input_list)
        t2 = time.time()
        if debug_info and i%cycles==0:
            logging.debug(str(len(boards)) + "boards' cycle time: " + str(1/(t2-t1)))



def test_list_generator(i, middle):
    """
    Can be used to generate running led effect on board
    arg i - led position (0-99)
    arg middle - the color value of the running led [R,G,B]
    """
    start = [0, 0, 0] * i
    end = [0, 0, 0] * (100 - 1 - i)
    return start + middle + end



