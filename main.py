__author__ = 'Mark Laane'

# Python 3.4.0
# PySerial 2.7
#Numpy 1.8.1
#Pillow 2.4.0

import tkinter
import logging
import configparser

from GUI_app import GUIapp
from matrix_controller import MatrixController
from game_controller import GameController
from webserver import MatrixWebserver

#Imported for configuring
from game_elements_library import Ball, Paddle


def csv_to_int_list(color_string):
    return [int(x.strip()) for x in color_string.split(',')]


def main():
    logging.basicConfig(format='[%(asctime)s] [%(threadName)13s] %(levelname)7s: %(message)s', level=logging.DEBUG)

    logging.info("Starting up...")

    logging.debug("Loading configuration...")
    config = configparser.ConfigParser()
    config.read('config.ini')
    gui_enabled = config["General"].getboolean("GUI")
    serial_ports = csv_to_int_list(config["Matrix"]["Serial ports"])
    Ball.configure(
        stroke_color=csv_to_int_list(config["Ball"]["Stroke color"]),
        fill_color=csv_to_int_list(config["Ball"]["Fill color"]),
        radius=float(config["Ball"]["Radius"])
    )
    Paddle.configure(
        width=float(config["Paddle"]["width"]),
        height=float(config["Paddle"]["height"])
    )
    logging.debug("Configuration loaded.")

    matrix_controller = MatrixController(serial_ports)

    game_controller = GameController(matrix_controller)

    #Webserver
    webserver = MatrixWebserver(game_controller, address="", port=8000)
    webserver.start()

    if gui_enabled:
        #GUI
        root = tkinter.Tk()
        root.geometry("300x750+50+50")
        root.title("LED control panel")
        app = GUIapp(root, game_controller)
        # Matrix controller will trigger GUI update when data changes
        matrix_controller.connect("data_update", app.update)

        game_controller.set_game_mode(GameController.Mode.breaker)

        logging.debug("Entering tkinter mainloop")
        root.mainloop()
        logging.debug("Tkinter mainloop has exited.")
    else:
        game_controller.set_game_mode(GameController.Mode.breaker)
        try:
            run = True
            while run:
                if input("Type 'q' to stop.") == "q":
                    run = False
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received.")
    logging.info("Stopping...")
    webserver.join()
    matrix_controller.stop()
    logging.info("Stopped.")



if __name__ == '__main__':
    main()
