__author__ = 'Mark Laane'

import time
import threading


class FpsManager:
    def __init__(self, fps_period=1.0):
        self.fps_period = fps_period

        self.current_fps = 0.0

        self._samples = []

        fps_thread = threading.Thread(target=self.update, name="FPS_thread", daemon=True)
        fps_thread.start()

    def cycle_complete(self):
        self._samples.append(time.time())

    def update(self):
        while True:
            curr_time = time.time()
            # filter out samples older than (curr_time-fps_period)
            self._samples = [cycle for cycle in self._samples if curr_time - cycle < self.fps_period]
            # find fps
            self.current_fps = len(self._samples) / self.fps_period
            time.sleep(0.02)

