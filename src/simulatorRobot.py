import math
from collections import deque
from queue import Queue
from threading import Event, Lock, Thread # --> not needed for simulatorRobot me thinks

class SimulatorRobot:

    def __init__(self):
        # starting coordinates --> make into params at some point
        self.x = 1129.0417
        self.y = 865.5514

        # coordinate database
        self.waypoints = dict()

        # add from file, to point database
        with open("point_database.txt",'r') as f:
            for line in f:
                arr = line.strip().split()
                self.waypoints[arr[0]] = dict()

                x_str = arr[1].split(".")
                y_str = arr[2].split(".")

                x_coord = x_str[0]
                y_coord = y_str[0]

                self.waypoints[arr[0]]["x"] = x_coord
                self.waypoints[arr[0]]["y"] = y_coord

        # queues
        self._target_queue = deque()
        self.current_target = None
        self.speed = 25.0  # sim only - pixels per animation frame
        self.status_log = "Robot initialized and stationary."

    def nav_to(self, location):
        loc = str(location)
        if loc in self.waypoints:
            self._target_queue.append((self.waypoints[loc]["x"], self.waypoints[loc]["y"]))
        else:
            self.status_log = "error"
