__author__ = 'Mark Laane'

# Python 3.4.0
# PySerial 2.7
# Numpy 1.8.1
# Pillow 2.4.0

import tkinter
import logging
import configparser

from GUI_app import GUIapp
from matrix_controller import MatrixController
from game_controller import GameController
from webserver import MatrixWebserver
from configure import configure_all


def main():
    logging.basicConfig(format='[%(asctime)s] [%(threadName)13s] %(levelname)7s: %(message)s', level=logging.DEBUG)

    logging.info("Starting up...")

    # ## Loading Configuration
    logging.debug("Loading configuration...")
    config = configparser.ConfigParser()
    config.read('config.ini')
    # General
    gui_enabled = config["General"].getboolean("GUI")
    configure_all(config)
    logging.debug("Configuration loaded.")

    ### Starting up Matrix
    matrix_controller = MatrixController()

    game_controller = GameController(matrix_controller)

    ### Starting up Webserver
    webserver = MatrixWebserver(game_controller, address="", port=8000)
    webserver.start()

    root = None
    if gui_enabled:
        ### Starting up GUI
        try:
            root = tkinter.Tk()
        except tkinter.TclError:
            logging.warning("Could not initialise Tk class - Disabling GUI")
            gui_enabled = False
        else:
            root.geometry("302x750+50+50")
            root.title("LED control panel")
            app = GUIapp(root, game_controller)
            # Matrix controller will trigger GUI update when data changes
            matrix_controller.connect("data_update", app.update)

    game_controller.set_game_mode(GameController.Mode.plasma)

    if gui_enabled:
        logging.debug("Entering tkinter mainloop")
        ### MAIN LOOP when GUI is enabled
        root.mainloop()
        logging.debug("Tkinter mainloop has exited.")
    else:
        try:
            ### MAIN LOOP when gui is disabled
            run = True
            while run:
                user_input = input("Type 'q' to stop or 'reset id' to reset all ID's.\n")
                if user_input == "q":
                    run = False
                elif user_input == "reset id":
                    matrix_controller.reset_id_all()
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt received.")

    ### STOPPING
    logging.info("Stopping...")
    webserver.join()
    matrix_controller.stop()
    logging.info("Stopped.")
    ### END


if __name__ == '__main__':
    main()
