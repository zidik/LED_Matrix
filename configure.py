__author__ = 'Mark'

from matrix_controller import MatrixController
from game_elements_library import Ball, Paddle
from catch_colors import FadingSymbol
from breaker import Breaker
from pong import Pong


def configure_all(config):
    conf_matrix(config["Matrix"])
    conf_ball(config["Ball"])
    conf_paddle(config["Paddle"])
    conf_pong(config["Pong"])
    conf_breaker(config["Breaker"])
    conf_catch_colors(config["Catch Colors"])


def csv_to_int_list(csv_string):
    if csv_string == '':
        return []
    else:
        return [int(x.strip()) for x in csv_string.split(',')]


def csv_to_float_list(color_string):
    return [float(x.strip()) for x in color_string.split(',')]


def conf_matrix(conf):
    MatrixController.serial_ports = csv_to_int_list(conf["Serial ports"])
    MatrixController.data_update_FPS = float(conf["Data Update FPS"])
    MatrixController.sensor_update_FPS = float(conf["Serial Update FPS"])
    MatrixController.dimensions = int(conf["Width"]), int(conf["Height"])


def conf_ball(conf):
    Ball.radius = float(conf["Radius"])
    Ball.stroke_color = csv_to_float_list(conf["Stroke color"])
    Ball.fill_color = csv_to_float_list(conf["Fill color"])


def conf_paddle(conf):
    Paddle.width = float(conf["width"])
    Paddle.height = float(conf["height"])
    Paddle.stroke_color = [
        csv_to_float_list(conf["Stroke color 0"]),
        csv_to_float_list(conf["Stroke color 1"])
    ]
    Paddle.fill_color = [
        csv_to_float_list(conf["Fill color 0"]),
        csv_to_float_list(conf["Fill color 1"])
    ]


def conf_pong(conf):
    Pong.lives = int(conf["Lives"])
    Pong.ball_speed = float(conf["Ball speed"])
    Pong.paddle_speed = float(conf["Paddle speed"])
    Pong.speed_change = float(conf["Speed change"])


def conf_breaker(conf):
    Breaker.lives = int(conf["Lives"])
    Breaker.brick_columns = int(conf["Columns"])
    Breaker.brick_rows = int(conf["Rows"])
    Breaker.ball_speed = float(conf["Ball speed"])
    Breaker.paddle_speed = float(conf["Paddle speed"])
    Breaker.speed_change = float(conf["Speed change"])
    Breaker.multi_ball_probability = float(conf["Multiple ball probability"])
    Breaker.brick_colors = [
        [csv_to_float_list(conf["Stroke color 0"]), csv_to_float_list(conf["Fill color 0"])],
        [csv_to_float_list(conf["Stroke color 1"]), csv_to_float_list(conf["Fill color 1"])]
    ]


def conf_catch_colors(conf):
    FadingSymbol.color_start = csv_to_float_list(conf["Symbol start color"])
    FadingSymbol.color_end = csv_to_float_list(conf["Symbol end color"])
    FadingSymbol.lifetime = float(conf["Symbol lifetime"])
    FadingSymbol.change_period = float(conf["Symbol change period"])
