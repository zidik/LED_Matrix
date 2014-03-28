__author__ = 'Mark'

import time


class FpsManager:
    def __init__(self, update_period=0.2, fps_period=1.0, string_var=None, string_var_text="{}FPS"):
        self.update_period = update_period
        self.fps_period = fps_period
        self.string_var = string_var
        self.string_var_text = string_var_text

        self.last_update = time.time()
        self.current_fps = 0
        self.data = []

    def cycle_complete(self):
        self.data.append(time.time())

        if time.time() - self.last_update > self.update_period:
            curr_time = time.time()
            self.data = [cycle for cycle in self.data if curr_time - cycle < self.fps_period]
            self.current_fps = len(self.data)

            # Can be omitted if it is called from somewhere else
            self.update_string_var()

    def update_string_var(self):
        if self.string_var is not None:
            self.string_var.set(self.string_var_text.format(self.current_fps))
