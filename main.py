__author__ = 'Mark Laane'

# Python 3.4.0
# PySerial 2.7
#Numpy 1.8.1
#Pillow 2.4.0


#List of ports to use:
# NB! In windows:
#  "3" will open COM4,
#  "4" will open COM5, etc

# Open port COM6
serial_ports = []

#Open ports COM2 and COM5
#serial_ports = [1,4]

GUI_ENABLED = False

import tkinter
import logging

from GUI_app import GUIapp
from matrix_controller import MatrixController
from game_controller import GameController
from webserver import MatrixWebserver


app = None


def main():
    global app
    logging.basicConfig(format='[%(asctime)s] [%(threadName)13s] %(levelname)7s: %(message)s', level=logging.DEBUG)

    logging.info("Starting up...")

    matrix_controller = MatrixController(serial_ports, update_gui)

    game_controller = GameController(matrix_controller)

    #Webserver
    webserver = MatrixWebserver(game_controller, address="", port=8000)
    webserver.start()

    if GUI_ENABLED:
        #GUI
        root = tkinter.Tk()
        root.geometry("300x750+50+50")
        root.title("LED control panel")
        app = GUIapp(root, game_controller)

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


def update_gui():
    global app
    if app is not None:
        app.update()


if __name__ == '__main__':
    main()
