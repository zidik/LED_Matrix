__author__ = 'Mark Laane'

#Python 3.4.0
#PySerial 2.7
#Numpy 1.8.1
#Pillow 2.4.0


#List of ports to use:
# NB! In windows:
#  "3" will open COM4,
#  "4" will open COM5, etc

#Open port COM5
serial_ports = [4]

#Open ports COM2 and COM5
#serial_ports = [1,4]


import tkinter
import logging
import matrix_controller


def main():
    logging.basicConfig(format='[%(asctime)s] [%(threadName)10s] %(levelname)7s: %(message)s', level=logging.DEBUG)

    logging.info("Starting up...")
    root = tkinter.Tk()
    root.geometry("300x750+50+50")
    root.title("LED control panel")

    app = matrix_controller.App(root, serial_ports)

    logging.debug("Entering tkinter mainloop")
    root.mainloop()

    logging.debug("Tkinter mainloop has exited...")
    app.stop()
    logging.info("Stopped.")


if __name__ == '__main__':
    main()
