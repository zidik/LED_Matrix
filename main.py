__author__ = 'Mark Laane'

import tkinter
import serial
import PIL.Image
import PIL.ImageTk
import numpy
import threading
import logging
import time

import fpsManager
import ledBoard

app_running = True


def main():
    global app_running
    logging.basicConfig(format='[%(asctime)s] [%(threadName)10s] %(levelname)7s: %(message)s', level=logging.DEBUG)

    logging.info("Starting up...")
    root = tkinter.Tk()
    root.geometry("700x550+50+50")
    root.title("LED control panel")

    #app.pack(fill=tkinter.BOTH, expand=1)

    app_running = True
    app = App(root)
    root.mainloop()
    #app.stop()  #TODO?
    app_running = False

    logging.info("Entering tkinter mainloop")
    root.mainloop()
    logging.info("Tkinter mainloop has exited...")


class App(object):
    def __init__(self, master, **kwargs):

        #Create random data
        brightness = 100
        self.data = numpy.array(numpy.random.random((10, 20, 3)) * brightness, dtype=numpy.uint8)
        self.data[1, 1] = numpy.array([255, 255, 255])

        self.data_updated = {'GUI': True, 'Serial': True} #TODO: make method

        serial_connections = [
            serial.Serial(port=4, baudrate=500000)
        ]

        number_of_boards = 4
        board_columns = 10

        self.board_buses = [
            [ledBoard.Board(128+number, number % board_columns, number // board_columns, serial_connections[0]) for number in range(0, number_of_boards)],
            []
        ]

        self.master = master
        self.frame = tkinter.Frame(self.master, width=600, height=400)
        self.frame.pack()
        self.canvas = tkinter.Canvas(self.frame, width=500, height=400)
        self.canvas.pack()

        self.photo = None  #Holds TkInter image for displaying in GUI

        #GUI FPS
        gui_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=gui_fps_var).pack()
        self.gui_fps = fpsManager.FpsManager(string_var=gui_fps_var, string_var_text="GUI: {} FPS")
        #Game FPS
        game_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=game_fps_var).pack()
        self.game_fps = fpsManager.FpsManager(string_var=game_fps_var,  string_var_text="Game: {} FPS")
        #Serial FPS
        serial_fps_var = tkinter.StringVar()
        tkinter.Label(self.frame, textvariable=serial_fps_var).pack()
        self.serial_fps = fpsManager.FpsManager(string_var=serial_fps_var,  string_var_text="Serial: {} FPS")

        # Start "Game"-Loop - updates data for displaying
        t = threading.Thread(target=self.update_data)
        t.start()

        # Start Serial-Loop - updates serial data
        t = threading.Thread(target=self.update_serial)
        t.start()

        # Start displaying in GUI
        self.master.after(0, self.animation)




    def animation(self):
        self.master.after(1, self.animation)

        ## UPDATE display if data has changed
        if self.data_updated['GUI']:
            self.data_updated['GUI'] = False
            im = PIL.Image.fromarray(self.data)
            im = im.resize((400, 200))
            #TODO: Currently causes Crash :(
            """
            self.photo = PIL.ImageTk.PhotoImage(image=im)
            self.canvas.create_image(0, 0, image=self.photo, anchor=tkinter.NW)
            #TODO: show Board-GUI fps
            """

        ##UPDATE END
        self.gui_fps.cycle_complete()

    def update_data(self):
        global app_running
        FPS = 10
        next_update = time.time()

        while app_running:
            try:
                ## UPDATE
                self.data = numpy.roll(self.data, -1, 1)
                self.data_updated = {'GUI': True, 'Serial': True}
                ##UPDATE END
                self.game_fps.cycle_complete()

                next_update += 1.0 / FPS
                sleeptime = next_update - time.time()
                if sleeptime > 0:
                    time.sleep(sleeptime)
            except Exception:
                if app_running:
                    raise
                else:
                    pass  #Supress errors when closing

    def update_serial(self):
        #Todo: make it sleep, so it wouldn't kill CPU
        logging.info("Serial update thread started up")
        while app_running:
            if self.data_updated['Serial']:
                # TODO! BUG? can be seen HERE IF ONLY ONE BOARD CONNECTED
                # Connectiong only one board and sending alot of data to it will make it flicker
                #(even if tha data is same)
                #Uncommenting next row will make serial send 100% of the
                self.data_updated['Serial'] = False

                for board_bus in self.board_buses:
                    for board in board_bus:
                        numpy_input = self.data[board.row * 10:board.row * 10 + 10, board.column * 10:board.column * 10 + 10]
                        input_list = self.numpy_to_input_list(numpy_input)
                        board.refresh_leds(input_list)
                self.serial_fps.cycle_complete()

        #Turn Off
        input_list = 100 * 3 * [0]
        for board_bus in self.board_buses:
            for board in board_bus:
                board.refresh_leds(input_list)

    @staticmethod
    def numpy_to_input_list(np_list):
        input_list = []
        reverse = False
        for row in np_list:
            if reverse:
                row = (list(row[::-1]))
            else:
                row = (list(row))
            for color in row:
                for color_element in color:
                    input_list.append(color_element >> 5)
            reverse = not reverse
        return input_list


if __name__ == '__main__':
    main()
