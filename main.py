__author__ = 'Mark Laane'

#Python 3.3.2
#Pillow 2.3.0
#Numpy 1.8.1
#PySerial 2.7

import tkinter
import logging

import matrix_controller


def main():
    logging.basicConfig(format='[%(asctime)s] [%(threadName)10s] %(levelname)7s: %(message)s', level=logging.DEBUG)

    logging.info("Starting up...")
    root = tkinter.Tk()
    root.geometry("700x550+50+50")
    root.title("LED control panel")

    #app.pack(fill=tkinter.BOTH, expand=1)

    app = matrix_controller.App(root)
    logging.info("Entering tkinter mainloop")
    root.mainloop()

    logging.info("Tkinter mainloop has exited...")
    app.stop()
    logging.info("END")


if __name__ == '__main__':
    main()
