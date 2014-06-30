__author__ = 'Mark Laane'

# Python 3.4.0
#PySerial 2.7
#Numpy 1.8.1
#Pillow 2.4.0


#List of ports to use:
# NB! In windows:
#  "3" will open COM4,
#  "4" will open COM5, etc

# Open port COM6
serial_ports = [2]

#Open ports COM2 and COM5
#serial_ports = [1,4]


import tkinter
import logging

from GUI_app import GUIapp
from matrix_controller import MatrixController


app = None


def main():
    global app
    logging.basicConfig(format='[%(asctime)s] [%(threadName)12s] %(levelname)7s: %(message)s', level=logging.DEBUG)

    logging.info("Starting up...")
    root = tkinter.Tk()
    root.geometry("300x750+50+50")
    root.title("LED control panel")

    matrix_controller = MatrixController(serial_ports, update_gui)
    app = GUIapp(root, matrix_controller)

    logging.debug("Entering tkinter mainloop")
    root.mainloop()

    logging.debug("Tkinter mainloop has exited...")
    app.stop()
    logging.info("Stopped.")


def update_gui():
    global app
    if app is not None:
        app.update()


if __name__ == '__main__':
    main()
